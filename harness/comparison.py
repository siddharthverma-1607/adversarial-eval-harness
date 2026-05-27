from typing import List
from .models import AttackResult

class ComparisonChange:
    def __init__(
        self,
        attack_id: str,
        attack_name: str,
        baseline_decision: str | None,
        new_decision: str | None,
        baseline_output: str | None,
        new_output: str | None,
        change_type: str,
    ):
        self.attack_id = attack_id
        self.attack_name = attack_name
        self.baseline_decision = baseline_decision
        self.new_decision = new_decision
        self.baseline_output = baseline_output
        self.new_output = new_output
        self.change_type = change_type
        self.shifted = change_type != "unchanged"


def compare_runs(baseline_results: List[AttackResult], new_results: List[AttackResult]) -> dict:
    baseline_map = {r.attack_id: r for r in baseline_results}
    new_map = {r.attack_id: r for r in new_results}
    changes = []
    attack_ids = sorted(set(baseline_map) | set(new_map))
    for attack_id in attack_ids:
        baseline = baseline_map.get(attack_id)
        new = new_map.get(attack_id)
        if baseline and not new:
            changes.append(
                ComparisonChange(
                    attack_id=attack_id,
                    attack_name=baseline.attack_name,
                    baseline_decision=baseline.decision,
                    new_decision=None,
                    baseline_output=baseline.output,
                    new_output=None,
                    change_type="removed",
                )
            )
            continue
        if new and not baseline:
            changes.append(
                ComparisonChange(
                    attack_id=attack_id,
                    attack_name=new.attack_name,
                    baseline_decision=None,
                    new_decision=new.decision,
                    baseline_output=None,
                    new_output=new.output,
                    change_type="added",
                )
            )
            continue
        change_type = "unchanged"
        if baseline.decision != new.decision:
            change_type = "decision_changed"
        elif baseline.output != new.output:
            change_type = "output_changed"
        change = ComparisonChange(
            attack_id=attack_id,
            attack_name=new.attack_name,
            baseline_decision=baseline.decision,
            new_decision=new.decision,
            baseline_output=baseline.output,
            new_output=new.output,
            change_type=change_type,
        )
        if change.change_type != "unchanged":
            changes.append(change)
    return {
        "baseline_run_id": baseline_results[0].run_id if baseline_results else None,
        "new_run_id": new_results[0].run_id if new_results else None,
        "changed_attacks": len(changes),
        "total_attacks": len(attack_ids),
        "changes": changes,
    }
