from datetime import datetime
from typing import List, Optional, Union
from sqlalchemy import select
from sqlalchemy.orm import Session

from .attacks import list_attacks
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
            payload = RunCreate.parse_obj(payload)
        model_name = payload.model_name or settings.model_name
        model_version = payload.model_version or settings.model_version
        run = Run(
            name=payload.name or "adversarial run",
            system_prompt=payload.system_prompt,
            model_name=model_name,
            model_version=model_version,
            status=RunStatus.pending,
        )
        with SessionLocal() as session:
            session.add(run)
            session.commit()
            session.refresh(run)
        return run

    def execute_run(self, run_id: int) -> Run:
        with SessionLocal() as session:
            run = session.get(Run, run_id)
            if not run:
                raise ValueError(f"Run {run_id} not found")
            if run.status == RunStatus.completed:
                return run
            run.status = RunStatus.running
            run.started_at = datetime.utcnow()
            session.add(run)
            session.commit()
            session.refresh(run)

            selected_attacks = self._select_attacks(run)
            results = []
            for attack in selected_attacks:
                prompt = attack.prompt
                output = self.model_client.run(run.system_prompt or "", prompt)
                decision, reason = judge_response(output)
                result = AttackResult(
                    run_id=run.id,
                    attack_id=attack.id,
                    attack_name=attack.name,
                    attack_description=attack.description,
                    prompt=prompt,
                    output=output,
                    decision=decision,
                    reason=reason,
                )
                session.add(result)
                results.append(result)
                session.commit()
            run.status = RunStatus.completed
            run.completed_at = datetime.utcnow()
            run.summary = self._build_summary(results)
            session.add(run)
            session.commit()
            session.refresh(run)
            return run

    def _select_attacks(self, run: Run) -> List:
        return list_attacks()

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
