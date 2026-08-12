from decimal import Decimal

import pytest

from qcal.gates import BudgetDecision, evaluate_cost_gate


@pytest.mark.parametrize("raw", [None, "", "twenty", "NaN", "Infinity", "-1", "0"])
def test_budget_gate_fails_closed_for_missing_or_invalid_budget(raw: str | None) -> None:
    decision = evaluate_cost_gate(raw_budget=raw, current_cost="0")

    assert decision.allowed is False
    assert decision.reason == "INVALID_BUDGET"


def test_budget_gate_defaults_to_twenty_dollars_only_when_requested() -> None:
    decision = evaluate_cost_gate(raw_budget=None, current_cost="0", allow_default=True)

    assert decision == BudgetDecision(
        allowed=True,
        reason="WITHIN_TARGET",
        budget=Decimal("20.00"),
        current_cost=Decimal("0.00"),
        action="CONTINUE",
    )


@pytest.mark.parametrize(
    ("current", "allowed", "reason", "action"),
    [
        ("9.99", True, "WITHIN_TARGET", "CONTINUE"),
        ("10.00", True, "TARGET_REACHED", "CONTINUE_WITH_CAUTION"),
        ("14.99", True, "ABOVE_TARGET", "CONTINUE_WITH_CAUTION"),
        ("15.00", False, "RETRY_STOP", "NO_NEW_COMPUTE"),
        ("19.99", False, "RETRY_STOP", "NO_NEW_COMPUTE"),
        ("20.00", False, "BUDGET_REACHED", "TEARDOWN"),
        ("20.01", False, "BUDGET_EXCEEDED", "TEARDOWN"),
    ],
)
def test_budget_gate_enforces_target_stop_and_teardown_thresholds(
    current: str, allowed: bool, reason: str, action: str
) -> None:
    decision = evaluate_cost_gate(raw_budget="20", current_cost=current)

    assert decision.allowed is allowed
    assert decision.reason == reason
    assert decision.action == action

