import pytest

from tax_model import (
    ReturnAmounts,
    calculate_eligible_dividend,
    calculate_eligible_investment,
    calculate_scenario,
    calculate_wage_increase_no_headcount_growth,
    calculate_wage_increase_with_headcount_growth,
)


def test_reference_example_from_project_notes():
    # 1,000억원 = 100,000백만원
    result = calculate_scenario(
        scenario_name="example",
        corporate_income=100_000,
        returns=ReturnAmounts(
            investment=30_000,
            dividend=10_000,
            wage_increase=5_800,
            cooperation_actual_spend=1_000,
        ),
        carryforward_excess=2_000,
        requested_current_reserve=6_000,
    )

    assert result.investment_included.current_unreturned_income == pytest.approx(31_200)
    assert result.investment_excluded.current_unreturned_income == pytest.approx(11_200)
    assert result.investment_excluded.current_taxable_unreturned_income == pytest.approx(3_200)
    assert result.investment_excluded.total_additional_tax == pytest.approx(640)


def test_excess_return_offsets_due_reserve():
    result = calculate_scenario(
        scenario_name="excess",
        corporate_income=10_000,
        returns=ReturnAmounts(investment=10_000),
        due_prior_reserve=3_000,
    ).investment_included

    # Target 8,000, investment 10,000 => excess 2,000.
    assert result.current_excess_return == pytest.approx(2_000)
    assert result.due_reserve_offset_by_excess == pytest.approx(2_000)
    assert result.due_reserve_shortfall == pytest.approx(1_000)
    assert result.due_reserve_additional_tax == pytest.approx(200)


def test_annual_total_subtraction_models():
    assert calculate_eligible_investment(1_000, [100, 200, 50]) == pytest.approx(650)
    assert calculate_eligible_dividend(1_000, [100, 50, 200]) == pytest.approx(650)

    with pytest.raises(ValueError):
        calculate_eligible_investment(100, [80, 30])


def test_wage_no_headcount_growth():
    assert calculate_wage_increase_no_headcount_growth(10_000, 11_000) == pytest.approx(1_000)
    assert calculate_wage_increase_no_headcount_growth(11_000, 10_000) == 0


def test_wage_with_headcount_growth():
    result = calculate_wage_increase_with_headcount_growth(
        prior_eligible_wages=10_000,
        current_eligible_wages=13_000,
        prior_headcount=100,
        current_headcount=110,
        average_wage_of_new_workers=200,
        youth_regular_worker_wage_increase=300,
        converted_regular_worker_wage_increase=100,
    )
    # Total increase 3,000; new component 10*200=2,000; existing 1,000.
    # Recognized = 1,000*1.5 + 2,000*2 + 300 + 100 = 5,900.
    assert result["new_worker_component"] == pytest.approx(2_000)
    assert result["existing_worker_component"] == pytest.approx(1_000)
    assert result["recognized_wage_increase"] == pytest.approx(5_900)
