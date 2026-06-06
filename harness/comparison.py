from typing import List
from .models import Run, AttackResult

class ComparisonChange:
    def __init__(self, attack_id: str, attack_name: str, baseline_decision: str, new_decision: str, baseline_output: str, new_output: str):
        self.attack_id = attack_id
        self.attack_name = attack_name
        self.baseline_decision = baseline_decision
        self.new_decision = new_decision
        self.baseline_output = baseline_output
        self.new_output = new_output
        self.shifted = baseline_decision != new_decision


def compare_runs(baseline_results: List[AttackResult], new_results: List[AttackResult]) -> dict:
    baseline_map = {r.attack_id: r for r in baseline_results}
    new_map = {r.attack_id: r for r in new_results}
    changes = []
    attack_ids = sorted(set(baseline_map) | set(new_map))
    for attack_id in attack_ids:
        baseline = baseline_map.get(attack_id)
        new = new_map.get(attack_id)
        if not baseline or not new:
            continue
        change = ComparisonChange(
            attack_id=attack_id,
            attack_name=new.attack_name if new else baseline.attack_name,
            baseline_decision=baseline.decision,
            new_decision=new.decision,
            baseline_output=baseline.output,
            new_output=new.output,
        )
        if change.shifted:
            changes.append(change)
    return {
        "baseline_run_id": baseline_results[0].run_id if baseline_results else None,
        "new_run_id": new_results[0].run_id if new_results else None,
        "changed_attacks": len(changes),
        "total_attacks": len(attack_ids),
        "changes": changes,
    }
