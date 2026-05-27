import argparse
from .runner import EvaluationRunner
from .comparison import compare_runs
from .db import init_db


def main() -> None:
    init_db()
    parser = argparse.ArgumentParser(description="Adversarial evaluation harness CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Create and execute a new run")
    run_parser.add_argument("--name", help="Run name")
    run_parser.add_argument("--system-prompt", help="System prompt override")
    run_parser.add_argument("--model-name", help="Model name override")
    run_parser.add_argument("--model-version", help="Model version override")

    compare_parser = subparsers.add_parser("compare", help="Compare two completed runs")
    compare_parser.add_argument("baseline_id", type=int, help="Baseline run ID")
    compare_parser.add_argument("new_id", type=int, help="New run ID")

    args = parser.parse_args()
    runner = EvaluationRunner()

    if args.command == "run":
        payload = {
            "name": args.name,
            "system_prompt": args.system_prompt,
            "model_name": args.model_name,
            "model_version": args.model_version,
        }
        run = runner.create_run(payload)
        executed_run = runner.execute_run(run.id)
        print(f"Completed run {executed_run.id} with status {executed_run.status}")
        print(executed_run.summary or "No summary available")
    elif args.command == "compare":
        baseline_results = runner.get_results(args.baseline_id)
        new_results = runner.get_results(args.new_id)
        comparison = compare_runs(baseline_results, new_results)
        print(f"Comparison baseline={comparison['baseline_run_id']} new={comparison['new_run_id']}")
        print(f"Changed attacks: {comparison['changed_attacks']} / {comparison['total_attacks']}")
        for item in comparison["changes"]:
            print(f"- {item.attack_id}: {item.baseline_decision} -> {item.new_decision}")

if __name__ == "__main__":
    main()
