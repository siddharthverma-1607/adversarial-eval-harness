import time
from .db import init_db, SessionLocal
from .models import Run, RunStatus
from .runner import EvaluationRunner
from .config import settings


def run_worker() -> None:
    init_db()
    runner = EvaluationRunner()
    print("Worker started: polling for pending runs")
    while True:
        with SessionLocal() as session:
            pending_run = session.query(Run).filter(Run.status == RunStatus.pending).order_by(Run.created_at).first()
            if pending_run:
                print(f"Found pending run {pending_run.id}: executing")
                try:
                    runner.execute_run(pending_run.id)
                    print(f"Completed run {pending_run.id}")
                except Exception as exc:
                    pending_run.status = RunStatus.failed
                    session.add(pending_run)
                    session.commit()
                    print(f"Run {pending_run.id} failed: {exc}")
            else:
                time.sleep(settings.worker_poll_interval)

if __name__ == "__main__":
    run_worker()
