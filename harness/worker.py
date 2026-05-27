import time
from .db import init_db
from .runner import EvaluationRunner
from .config import settings


def run_worker() -> None:
    init_db()
    runner = EvaluationRunner()
    print("Worker started: polling for pending runs")
    while True:
        run_id = runner.claim_next_pending_run()
        if run_id:
            print(f"Claimed pending run {run_id}: executing")
            try:
                runner.execute_run(run_id, already_claimed=True)
                print(f"Completed run {run_id}")
            except Exception as exc:
                print(f"Run {run_id} failed: {exc}")
        else:
            time.sleep(settings.worker_poll_interval)

if __name__ == "__main__":
    run_worker()
