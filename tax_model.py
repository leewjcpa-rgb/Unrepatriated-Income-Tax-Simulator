"""Core calculation logic for the unrepatriated income scenario simulator.

All monetary amounts are expressed in KRW millions (백만원).
The module intentionally separates tax logic from the Streamlit UI so that
calculations can be unit-tested and reused.

Legal basis snapshot: Korean Restriction of Special Taxation Act Article 100-32
and its Enforcement Decree, as in force on 2026-07-20.
This is an educational planning aid, not a tax return engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal


Method = Literal["investment_included", "investment_excluded"]


@dataclass(frozen=True)
class TaxParameters:
    """Law-driven parameters centralized for easier annual maintenance."""

    investment_included_rate: float = 0.80
    investment_excluded_rate: float = 0.30
    additional_tax_rate: float = 0.20
    cooperation_multiplier: float = 3.00
    existing_worker_multiplier: float = 1.50
    new_worker_multiplier: float = 2.00


@dataclass(frozen=True)
class ReturnAmounts:
    """Recognized return amounts used in the Article 100-32 calculation."""

    investment: float = 0.0
    dividend: float = 0.0
    wage_increase: float = 0.0
    cooperation_actual_spend: float = 0.0

    def validated(self) -> "ReturnAmounts":
        values = {
            "investment": self.investment,
            "dividend": self.dividend,
            "wage_increase": self.wage_increase,
            "cooperation_actual_spend": self.cooperation_actual_spend,
        }
        for name, value in values.items():
            if value < 0:
                raise ValueError(f"{name} cannot be negative")
        return self

    def cooperation_recognized(self, params: TaxParameters) -> float:
        return self.cooperation_actual_spend * params.cooperation_multiplier

    def common_return(self, params: TaxParameters) -> float:
        """Return amount recognized under both methods, excluding investment."""
        return (
            self.dividend
            + self.wage_increase
            + self.cooperation_recognized(params)
        )


@dataclass(frozen=True)
class MethodResult:
    """Calculated result for one statutory method and one income scenario."""

    method: Method
    corporate_income: float
    target_return: float
    recognized_return: float
    raw_balance: float
    current_unreturned_income: float
    current_excess_return: float
    due_reserve_amount: float
    due_reserve_offset_by_excess: float
    due_reserve_shortfall: float
    carryforward_excess_available: float
    carryforward_excess_used: float
    current_reserve_requested: float
    current_reserve_used: float
    current_taxable_unreturned_income: float
    current_additional_tax: float
    due_reserve_additional_tax: float
    total_additional_tax: float
    unused_carryforward_excess: float
    current_excess_after_due_reserve: float
    next_excess_pool_before_expiry_review: float
    additional_return_needed: float


@dataclass(frozen=True)
class ScenarioResult:
    """Paired calculation for both methods."""

    scenario_name: str
    corporate_income: float
    investment_included: MethodResult
    investment_excluded: MethodResult
    investment_break_even: float


def _nonnegative(value: float, name: str) -> float:
    if value < 0:
        raise ValueError(f"{name} cannot be negative")
    return float(value)


def calculate_eligible_investment(total_spend: float, exclusions: Iterable[float]) -> float:
    """Calculate a provisional eligible investment amount from annual totals."""
    total = _nonnegative(total_spend, "total_spend")
    excluded = 0.0
    for value in exclusions:
        excluded += _nonnegative(value, "investment exclusion")
    if excluded > total + 1e-9:
        raise ValueError("Investment exclusions cannot exceed total investment spend")
    return total - excluded


def calculate_eligible_dividend(total_declared_or_recorded: float, exclusions: Iterable[float]) -> float:
    """Calculate a provisional eligible cash-dividend amount from annual totals."""
    total = _nonnegative(total_declared_or_recorded, "total_declared_or_recorded")
    excluded = 0.0
    for value in exclusions:
        excluded += _nonnegative(value, "dividend exclusion")
    if excluded > total + 1e-9:
        raise ValueError("Dividend exclusions cannot exceed the total dividend amount")
    return total - excluded


def calculate_wage_increase_no_headcount_growth(
    prior_eligible_wages: float,
    current_eligible_wages: float,
) -> float:
    """Recognized wage increase when eligible headcount did not increase."""
    prior = _nonnegative(prior_eligible_wages, "prior_eligible_wages")
    current = _nonnegative(current_eligible_wages, "current_eligible_wages")
    return max(current - prior, 0.0)


def calculate_wage_increase_with_headcount_growth(
    *,
    prior_eligible_wages: float,
    current_eligible_wages: float,
    prior_headcount: float,
    current_headcount: float,
    average_wage_of_new_workers: float,
    youth_regular_worker_wage_increase: float = 0.0,
    converted_regular_worker_wage_increase: float = 0.0,
    params: TaxParameters | None = None,
) -> dict[str, float]:
    """Calculate the wage-increase components when eligible headcount increased.

    The new-worker component is capped at the total eligible wage increase.
    The youth and converted-regular-worker additions are entered as amounts that
    have already passed the underlying eligibility review.
    """
    p = params or TaxParameters()
    prior_wages = _nonnegative(prior_eligible_wages, "prior_eligible_wages")
    current_wages = _nonnegative(current_eligible_wages, "current_eligible_wages")
    prior_count = _nonnegative(prior_headcount, "prior_headcount")
    current_count = _nonnegative(current_headcount, "current_headcount")
    avg_new_wage = _nonnegative(average_wage_of_new_workers, "average_wage_of_new_workers")
    youth = _nonnegative(youth_regular_worker_wage_increase, "youth_regular_worker_wage_increase")
    converted = _nonnegative(
        converted_regular_worker_wage_increase,
        "converted_regular_worker_wage_increase",
    )

    total_increase = max(current_wages - prior_wages, 0.0)
    headcount_increase = max(current_count - prior_count, 0.0)
    new_worker_component = min(headcount_increase * avg_new_wage, total_increase)
    existing_worker_component = max(total_increase - new_worker_component, 0.0)

    recognized = (
        existing_worker_component * p.existing_worker_multiplier
        + new_worker_component * p.new_worker_multiplier
        + youth
        + converted
    )
    return {
        "total_wage_increase": total_increase,
        "headcount_increase": headcount_increase,
        "existing_worker_component": existing_worker_component,
        "new_worker_component": new_worker_component,
        "youth_regular_worker_addition": youth,
        "converted_regular_worker_addition": converted,
        "recognized_wage_increase": recognized,
    }


def calculate_method(
    *,
    method: Method,
    corporate_income: float,
    returns: ReturnAmounts,
    due_prior_reserve: float = 0.0,
    carryforward_excess: float = 0.0,
    requested_current_reserve: float = 0.0,
    params: TaxParameters | None = None,
) -> MethodResult:
    """Calculate one method for one scenario.

    Modeling assumptions:
    - A prior reserve whose settlement deadline arrives in the current year is
      offset only by the current year's statutory excess return, consistent with
      Article 100-32(6).
    - For a positive current-year balance, carried excess return is shown as used
      before a newly requested current reserve. This is a dashboard allocation
      convention for transparency; expiry/vintage ordering must be reviewed in a
      real filing.
    """
    p = params or TaxParameters()
    income = _nonnegative(corporate_income, "corporate_income")
    due_reserve = _nonnegative(due_prior_reserve, "due_prior_reserve")
    cf_excess = _nonnegative(carryforward_excess, "carryforward_excess")
    requested_reserve = _nonnegative(requested_current_reserve, "requested_current_reserve")
    r = returns.validated()

    if method == "investment_included":
        target = income * p.investment_included_rate
        recognized = r.investment + r.common_return(p)
    elif method == "investment_excluded":
        target = income * p.investment_excluded_rate
        recognized = r.common_return(p)
    else:
        raise ValueError(f"Unsupported method: {method}")

    raw = target - recognized
    current_unreturned = max(raw, 0.0)
    current_excess = max(-raw, 0.0)

    # Settlement of a reserve whose two-year settlement deadline arrives now.
    due_offset = min(due_reserve, current_excess)
    due_shortfall = max(due_reserve - due_offset, 0.0)
    current_excess_after_due = max(current_excess - due_offset, 0.0)

    # Current-year positive balance reductions. Apply carried excess first in the
    # dashboard so the use of expiring balances is visible.
    cf_used = min(cf_excess, current_unreturned)
    after_cf = max(current_unreturned - cf_used, 0.0)
    current_reserve_used = min(requested_reserve, after_cf)
    current_taxable = max(after_cf - current_reserve_used, 0.0)

    current_tax = current_taxable * p.additional_tax_rate
    due_tax = due_shortfall * p.additional_tax_rate
    total_tax = current_tax + due_tax

    unused_cf = max(cf_excess - cf_used, 0.0)
    next_excess_pool = unused_cf + current_excess_after_due

    return MethodResult(
        method=method,
        corporate_income=income,
        target_return=target,
        recognized_return=recognized,
        raw_balance=raw,
        current_unreturned_income=current_unreturned,
        current_excess_return=current_excess,
        due_reserve_amount=due_reserve,
        due_reserve_offset_by_excess=due_offset,
        due_reserve_shortfall=due_shortfall,
        carryforward_excess_available=cf_excess,
        carryforward_excess_used=cf_used,
        current_reserve_requested=requested_reserve,
        current_reserve_used=current_reserve_used,
        current_taxable_unreturned_income=current_taxable,
        current_additional_tax=current_tax,
        due_reserve_additional_tax=due_tax,
        total_additional_tax=total_tax,
        unused_carryforward_excess=unused_cf,
        current_excess_after_due_reserve=current_excess_after_due,
        next_excess_pool_before_expiry_review=next_excess_pool,
        additional_return_needed=current_taxable,
    )


def calculate_scenario(
    *,
    scenario_name: str,
    corporate_income: float,
    returns: ReturnAmounts,
    due_prior_reserve: float = 0.0,
    carryforward_excess: float = 0.0,
    requested_current_reserve: float = 0.0,
    params: TaxParameters | None = None,
) -> ScenarioResult:
    p = params or TaxParameters()
    income = _nonnegative(corporate_income, "corporate_income")
    included = calculate_method(
        method="investment_included",
        corporate_income=income,
        returns=returns,
        due_prior_reserve=due_prior_reserve,
        carryforward_excess=carryforward_excess,
        requested_current_reserve=requested_current_reserve,
        params=p,
    )
    excluded = calculate_method(
        method="investment_excluded",
        corporate_income=income,
        returns=returns,
        due_prior_reserve=due_prior_reserve,
        carryforward_excess=carryforward_excess,
        requested_current_reserve=requested_current_reserve,
        params=p,
    )
    break_even = income * (
        p.investment_included_rate - p.investment_excluded_rate
    )
    return ScenarioResult(
        scenario_name=scenario_name,
        corporate_income=income,
        investment_included=included,
        investment_excluded=excluded,
        investment_break_even=break_even,
    )
