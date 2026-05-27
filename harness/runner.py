from datetime import datetime
import json
import time
from typing import List, Optional, Union
from sqlalchemy import select

from .attacks import get_attack_by_id, list_attacks
from .config import settings
from .db import SessionLocal
from .judge import judge_response
from .llm import create_model_client
from .models import Run, AttackResult, RunStatus
from .schemas import RunCreate

class EvaluationRunner:
    def __init__(self) -> None:
        self.model_client = create_model_client()

    def create_run(self, payload: Union[RunCreate, dict]) -> Run:
        if isinstance(payload, dict):
            payload = RunCreate.model_validate(payload)
        model_name = payload.model_name or settings.model_name
        model_version = payload.model_version or settings.model_version
        attack_ids = payload.attack_ids or [attack.id for attack in list_attacks()]
        unknown_attack_ids = [attack_id for attack_id in attack_ids if not get_attack_by_id(attack_id)]
        if unknown_attack_ids:
            raise ValueError(f"Unknown attack IDs: {', '.join(unknown_attack_ids)}")
        run = Run(
            name=payload.name or "adversarial run",
            system_prompt=payload.system_prompt,
            selected_attack_ids=json.dumps(attack_ids),
            model_provider=settings.model_type.value,
            model_name=model_name,
            model_version=model_version,
            status=RunStatus.pending,
        )
        with SessionLocal() as session:
            session.add(run)
            session.commit()
            session.refresh(run)
        return run

    def claim_next_pending_run(self) -> Optional[int]:
        with SessionLocal() as session:
            stmt = (
                select(Run)
                .where(Run.status == RunStatus.pending)
                .order_by(Run.created_at)
                .with_for_update(skip_locked=True)
            )
            run = session.execute(stmt).scalars().first()
            if not run:
                return None
            run.status = RunStatus.running
            run.started_at = datetime.utcnow()
            session.add(run)
            session.commit()
            return run.id

    def execute_run(self, run_id: int, already_claimed: bool = False) -> Run:
        with SessionLocal() as session:
            run = session.get(Run, run_id)
            if not run:
                raise ValueError(f"Run {run_id} not found")
            if run.status == RunStatus.completed:
                return run
            if run.status == RunStatus.running and not already_claimed:
                return run
            if run.status == RunStatus.pending:
                run.status = RunStatus.running
                run.started_at = datetime.utcnow()
                session.add(run)
                session.commit()
                session.refresh(run)

            try:
                selected_attacks = self._select_attacks(run)
                results = []
                for attack in selected_attacks:
                    started = time.perf_counter()
                    output = ""
                    error = None
                    decision = "unknown"
                    reason = "execution failed"
                    try:
                        output = self.model_client.run(run.system_prompt or "", attack.prompt, run.model_name)
                        decision, reason = judge_response(output)
                    except Exception as exc:
                        error = str(exc)
                    latency_ms = (time.perf_counter() - started) * 1000
                    result = AttackResult(
                        run_id=run.id,
                        attack_id=attack.id,
                        attack_name=attack.name,
                        attack_description=attack.description,
                        prompt=attack.prompt,
                        output=output,
                        decision=decision,
                        reason=reason,
                        latency_ms=latency_ms,
                        error=error,
                    )
                    session.add(result)
                    results.append(result)
                    session.commit()

                run.status = RunStatus.completed if all(result.error is None for result in results) else RunStatus.failed
                run.completed_at = datetime.utcnow()
                run.summary = self._build_summary(results)
                session.add(run)
                session.commit()
                session.refresh(run)
                return run
            except Exception:
                run.status = RunStatus.failed
                run.completed_at = datetime.utcnow()
                run.summary = "run failed before all attacks completed"
                session.add(run)
                session.commit()
                raise

    def _select_attacks(self, run: Run) -> List:
        if not run.selected_attack_ids:
            return list_attacks()
        attack_ids = json.loads(run.selected_attack_ids)
        return [get_attack_by_id(attack_id) for attack_id in attack_ids if get_attack_by_id(attack_id)]

    def _build_summary(self, results: List[AttackResult]) -> str:
        counts = {"safe": 0, "jailbreak": 0, "unknown": 0}
        for result in results:
            counts[result.decision] = counts.get(result.decision, 0) + 1
        return f"safe={counts['safe']} jailbreak={counts['jailbreak']} unknown={counts['unknown']}"

    def list_runs(self) -> List[Run]:
        with SessionLocal() as session:
            return session.execute(select(Run).order_by(Run.created_at.desc())).scalars().all()

    def get_run(self, run_id: int) -> Optional[Run]:
        with SessionLocal() as session:
            return session.get(Run, run_id)

    def get_results(self, run_id: int) -> List[AttackResult]:
        with SessionLocal() as session:
            return session.execute(
                select(AttackResult).where(AttackResult.run_id == run_id)
            ).scalars().all()
