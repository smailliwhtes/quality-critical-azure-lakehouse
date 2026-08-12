"""Fail-closed execution gates for the bounded Azure build."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

DEFAULT_BUDGET_USD = Decimal("20.00")
TARGET_COST_USD = Decimal("10.00")
RETRY_STOP_USD = Decimal("15.00")


@dataclass(frozen=True, slots=True)
class BudgetDecision:
    """A machine-readable authorization decision for new cloud work."""

    allowed: bool
    reason: str
    budget: Decimal | None
    current_cost: Decimal | None
    action: str


def _positive_money(raw: str | None) -> Decimal | None:
    if raw is None or not raw.strip():
        return None
    try:
        parsed = Decimal(raw)
    except InvalidOperation:
        return None
    if not parsed.is_finite() or parsed <= 0:
        return None
    return parsed.quantize(Decimal("0.01"))


def _nonnegative_money(raw: str | None) -> Decimal | None:
    if raw is None or not raw.strip():
        return None
    try:
        parsed = Decimal(raw)
    except InvalidOperation:
        return None
    if not parsed.is_finite() or parsed < 0:
        return None
    return parsed.quantize(Decimal("0.01"))


def evaluate_cost_gate(
    *, raw_budget: str | None, current_cost: str | None, allow_default: bool = False
) -> BudgetDecision:
    """Evaluate the project's target, retry-stop, and teardown thresholds.

    Callers must pass an explicit numeric budget unless ``allow_default`` is set by a
    controlled wrapper that intentionally applies the documented $20 default.
    """

    budget = _positive_money(raw_budget)
    if budget is None and allow_default and raw_budget is None:
        budget = DEFAULT_BUDGET_USD
    if budget is None:
        return BudgetDecision(False, "INVALID_BUDGET", None, None, "STOP")

    cost = _nonnegative_money(current_cost)
    if cost is None:
        return BudgetDecision(False, "INVALID_CURRENT_COST", budget, None, "STOP")

    if cost > budget:
        return BudgetDecision(False, "BUDGET_EXCEEDED", budget, cost, "TEARDOWN")
    if cost == budget:
        return BudgetDecision(False, "BUDGET_REACHED", budget, cost, "TEARDOWN")
    if cost >= RETRY_STOP_USD:
        return BudgetDecision(False, "RETRY_STOP", budget, cost, "NO_NEW_COMPUTE")
    if cost > TARGET_COST_USD:
        return BudgetDecision(True, "ABOVE_TARGET", budget, cost, "CONTINUE_WITH_CAUTION")
    if cost == TARGET_COST_USD:
        return BudgetDecision(True, "TARGET_REACHED", budget, cost, "CONTINUE_WITH_CAUTION")
    return BudgetDecision(True, "WITHIN_TARGET", budget, cost, "CONTINUE")

