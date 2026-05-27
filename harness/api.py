from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .db import init_db
from .runner import EvaluationRunner
from .attacks import list_attacks
from .schemas import RunCreate, RunRead, AttackDefinition, AttackResultRead, ComparisonSummary
from .comparison import compare_runs

app = FastAPI(title="Adversarial Eval Harness")
runner = EvaluationRunner()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event() -> None:
    init_db()

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

@app.get("/attacks", response_model=list[AttackDefinition])
def api_list_attacks() -> list[AttackDefinition]:
    return list_attacks()

@app.post("/runs", response_model=RunRead, status_code=status.HTTP_201_CREATED)
def create_run(payload: RunCreate) -> RunRead:
    try:
        run = runner.create_run(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return run

@app.post("/runs/{run_id}/start", response_model=RunRead)
def start_run(run_id: int) -> RunRead:
    try:
        run = runner.execute_run(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return run

@app.get("/runs", response_model=list[RunRead])
def get_runs() -> list[RunRead]:
    return runner.list_runs()

@app.get("/runs/{run_id}", response_model=RunRead)
def get_run(run_id: int) -> RunRead:
    run = runner.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run

@app.get("/runs/{run_id}/results", response_model=list[AttackResultRead])
def get_results(run_id: int) -> list[AttackResultRead]:
    run = runner.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return runner.get_results(run_id)

@app.get("/runs/{run_id}/compare", response_model=ComparisonSummary)
def compare_run(run_id: int, baseline_id: int) -> ComparisonSummary:
    baseline = runner.get_run(baseline_id)
    if not baseline:
        raise HTTPException(status_code=404, detail="Baseline run not found")
    new_run = runner.get_run(run_id)
    if not new_run:
        raise HTTPException(status_code=404, detail="Run not found")
    baseline_results = runner.get_results(baseline_id)
    new_results = runner.get_results(run_id)
    diff = compare_runs(baseline_results, new_results)
    return JSONResponse(
        content={
            "baseline_run_id": diff["baseline_run_id"],
            "new_run_id": diff["new_run_id"],
            "changed_attacks": diff["changed_attacks"],
            "total_attacks": diff["total_attacks"],
            "changes": [
                {
                    "attack_id": change.attack_id,
                    "attack_name": change.attack_name,
                    "baseline_decision": change.baseline_decision,
                    "new_decision": change.new_decision,
                    "baseline_output": change.baseline_output,
                    "new_output": change.new_output,
                    "change_type": change.change_type,
                    "shifted": change.shifted,
                }
                for change in diff["changes"]
            ],
        }
    )
