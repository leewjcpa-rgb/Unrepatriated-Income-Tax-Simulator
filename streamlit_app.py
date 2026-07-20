"""Streamlit UI for the 미환류소득 시나리오 프로그램."""

from __future__ import annotations

import html
from typing import Iterable

import pandas as pd
import streamlit as st

from tax_model import (
    ReturnAmounts,
    TaxParameters,
    calculate_eligible_dividend,
    calculate_eligible_investment,
    calculate_scenario,
    calculate_wage_increase_no_headcount_growth,
    calculate_wage_increase_with_headcount_growth,
)


APP_VERSION = "0.2.1"
UNIT = "백만원"
PARAMS = TaxParameters()


st.set_page_config(
    page_title="미환류소득 시나리오 프로그램",
    page_icon="🧮",
    layout="wide",
)

st.markdown(
    """
<style>
.block-container {padding-top: 1.4rem; padding-bottom: 3rem;}
.small-note {font-size: 0.88rem; color: #6b7280;}
.amount-card {
    border: 1px solid rgba(128,128,128,.25);
    border-radius: .85rem;
    padding: 1.05rem 1.15rem;
    margin-bottom: .65rem;
    background: rgba(128,128,128,.035);
}
.amount-label {
    font-size: 1rem;
    font-weight: 500;
    margin-bottom: .35rem;
}
.amount-value {
    font-size: 2.35rem;
    font-weight: 500;
    line-height: 1.15;
    letter-spacing: -.02em;
    white-space: nowrap;
}
.amount-unit {
    font-size: 1rem;
    font-weight: 400;
    margin-left: .25rem;
}
.amount-note {
    font-size: .9rem;
    margin-top: .4rem;
    color: #6b7280;
}
.scenario-card {
    border: 1px solid rgba(128,128,128,.25);
    border-radius: .85rem;
    padding: 1rem 1.1rem;
    height: 100%;
    background: rgba(128,128,128,.025);
}
.scenario-title {
    font-size: 1.1rem;
    font-weight: 650;
    margin-bottom: .75rem;
}
.scenario-row {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    padding: .42rem 0;
    border-bottom: 1px solid rgba(128,128,128,.14);
}
.scenario-row:last-child {border-bottom: 0;}
.scenario-label {font-size: .94rem; color: #4b5563;}
.scenario-number {font-size: .98rem; font-weight: 600; text-align: right;}
@media (max-width: 700px) {
    .amount-value {font-size: 1.9rem;}
}
</style>
""",
    unsafe_allow_html=True,
)


def unit_label(label: str) -> str:
    """Append the monetary unit to user-editable amount labels."""
    if f"({UNIT})" in label:
        return label
    return f"{label} ({UNIT})"


def money_input(label: str, *, key: str, value: float = 0.0, help_text: str | None = None) -> float:
    return float(
        st.number_input(
            unit_label(label),
            min_value=0.0,
            value=float(value),
            step=100.0,
            format="%.1f",
            key=key,
            help=help_text,
        )
    )


def fmt_number(value: float) -> str:
    return f"{value:,.1f}"


def fmt(value: float) -> str:
    return f"{fmt_number(value)} {UNIT}"


def render_amount_card(label: str, value: float, note: str | None = None) -> None:
    note_html = f'<div class="amount-note">{note}</div>' if note else ""
    st.markdown(
        f"""
<div class="amount-card">
  <div class="amount-label">{label}</div>
  <div class="amount-value">{fmt_number(value)}<span class="amount-unit">{UNIT}</span></div>
  {note_html}
</div>
""",
        unsafe_allow_html=True,
    )


def calculate_with_cap(total: float, exclusions: Iterable[float], calculator, label: str) -> tuple[float, str | None]:
    try:
        return calculator(total, exclusions), None
    except ValueError as exc:
        return 0.0, f"{label}: {exc}"


st.title("미환류소득 시나리오 프로그램")
st.caption(
    "예상 기업소득과 환류계획을 입력해 투자포함형·투자제외형의 미환류소득과 추가 법인세를 비교합니다. "
    f"모든 금액 단위는 {UNIT}입니다."
)

st.info(
    "본 앱은 2026년 7월 20일 기준 법령을 토대로 만든 교육·의사결정 보조용 시뮬레이터입니다. "
    "적용대상 여부, 기업소득, 투자·배당·임금·상생협력의 세법상 인정 여부와 실제 신고금액은 세무전문가의 별도 검토가 필요합니다."
)

with st.sidebar:
    st.subheader("법령 상수")
    st.write(f"투자포함형 환류기준율: **{PARAMS.investment_included_rate:.0%}**")
    st.write(f"투자제외형 환류기준율: **{PARAMS.investment_excluded_rate:.0%}**")
    st.write(f"추가 법인세율: **{PARAMS.additional_tax_rate:.0%}**")
    st.write(f"상생협력 인정배수: **×{PARAMS.cooperation_multiplier:.0f}**")
    st.write(f"기존근로자 가중치: **×{PARAMS.existing_worker_multiplier:.1f}**")
    st.write(f"신규근로자 가중치: **×{PARAMS.new_worker_multiplier:.1f}**")
    st.divider()
    st.caption(f"Version {APP_VERSION}")

input_tab, result_tab, scenario_tab, basis_tab = st.tabs(
    ["① 입력 및 상세 산정", "② 기준 결과", "③ 시나리오 비교", "④ 계산 근거·한계"]
)

warnings: list[str] = []

with input_tab:
    st.subheader("기업소득 및 이월항목")
    c1, c2 = st.columns(2)
    with c1:
        base_income = money_input(
            "기준 예상 기업소득",
            key="base_income",
            value=100_000.0,
            help_text="법인세법상 각 사업연도 소득금액에 미환류소득 관련 가감항목을 반영한 기업소득을 입력합니다.",
        )
        due_prior_reserve = money_input(
            "당기 정산기한이 도래한 차기환류적립금",
            key="due_prior_reserve",
            help_text="과거에 설정했고 당기에 2개 사업연도 정산기한이 도래하는 금액입니다. 당기 초과환류액으로 정산되는 구조를 반영합니다.",
        )
    with c2:
        carryforward_excess = money_input(
            "당기 사용 가능한 이월 초과환류액",
            key="carryforward_excess",
            help_text="발생연도·소멸기한 검토를 마친 사용 가능 금액을 입력합니다.",
        )
        requested_current_reserve = money_input(
            "당기 새로 설정할 차기환류적립금",
            key="requested_current_reserve",
            help_text="당기 미환류소득 중 다음 2개 사업연도에 환류할 목적으로 새로 적립하려는 금액입니다.",
        )

    st.divider()
    st.subheader("환류항목")

    investment_col, dividend_col = st.columns(2)

    with investment_col:
        st.markdown("### 투자액")
        investment_mode = st.radio(
            "투자액 입력 방식",
            ["상세 계산", "인정금액 직접 입력"],
            horizontal=True,
            key="investment_mode",
        )
        if investment_mode == "인정금액 직접 입력":
            eligible_investment = money_input(
                "세법 검토 완료 적격 투자액",
                key="investment_direct",
            )
        else:
            total_investment = money_input(
                "당기 투자 관련 실제 지출액",
                key="investment_total",
                help_text="여러 사업연도에 걸친 투자는 당기 실제 지출액 기준으로 입력합니다.",
            )
            with st.expander("제외항목 입력", expanded=True):
                used_assets = money_input("중고자산", key="inv_used")
                overseas_assets = money_input("해외사업장 사용 자산", key="inv_overseas")
                land_excluded = money_input("토지·영업권 등 제외대상", key="inv_land")
                operating_lease = money_input("금융리스 외 리스자산", key="inv_lease")
                nonbusiness = money_input("비사업용·기타 명확한 제외자산", key="inv_nonbusiness")
                other_inv_exclusion = money_input("기타 제외금액", key="inv_other")
            eligible_investment, inv_error = calculate_with_cap(
                total_investment,
                [used_assets, overseas_assets, land_excluded, operating_lease, nonbusiness, other_inv_exclusion],
                calculate_eligible_investment,
                "투자액",
            )
            if inv_error:
                warnings.append(inv_error)
            render_amount_card("잠정 적격 투자액", eligible_investment)
            st.caption("연간 합계형 간편 산정입니다. 제외항목 중복입력과 개별 자산 적격성은 별도 검토가 필요합니다.")

    with dividend_col:
        st.markdown("### 배당액")
        dividend_mode = st.radio(
            "배당액 입력 방식",
            ["상세 계산", "인정금액 직접 입력"],
            horizontal=True,
            key="dividend_mode",
        )
        if dividend_mode == "인정금액 직접 입력":
            eligible_dividend = money_input(
                "세법 검토 완료 적격 금전배당액",
                key="dividend_direct",
            )
        else:
            total_dividend = money_input(
                "당기 배당 결의·계상 총액",
                key="dividend_total",
            )
            with st.expander("제외항목 입력", expanded=True):
                stock_dividend = money_input("주식배당", key="div_stock")
                capital_reserve_dividend = money_input("자본준비금 감액배당", key="div_capital")
                legal_reserve_dividend = money_input("이익준비금 감액배당", key="div_legal")
                unpaid_dividend = money_input("당기 말 미지급배당금", key="div_unpaid")
                other_div_exclusion = money_input("기타 제외금액", key="div_other")
            eligible_dividend, div_error = calculate_with_cap(
                total_dividend,
                [stock_dividend, capital_reserve_dividend, legal_reserve_dividend, unpaid_dividend, other_div_exclusion],
                calculate_eligible_dividend,
                "배당액",
            )
            if div_error:
                warnings.append(div_error)
            render_amount_card("잠정 적격 금전배당액", eligible_dividend)
            st.caption("결의·계상 총액에서 비금전·준비금 감액·미지급 금액 등을 차감하는 연간 합계형 간편 산정입니다.")

    wage_col, cooperation_col = st.columns(2)

    with wage_col:
        st.markdown("### 임금증가 인정액")
        wage_mode = st.radio(
            "임금 입력 방식",
            ["상세 계산", "인정금액 직접 입력"],
            horizontal=True,
            key="wage_mode",
        )
        wage_details: dict[str, float] = {}
        if wage_mode == "인정금액 직접 입력":
            eligible_wage = money_input(
                "세법 검토 완료 임금증가 인정액",
                key="wage_direct",
            )
        else:
            headcount_growth = st.radio(
                "당기 상시근로자 수가 전기보다 증가했습니까?",
                ["증가하지 않음", "증가함"],
                horizontal=True,
                key="headcount_growth",
            )
            prior_wages = money_input("전기 적격 상시근로자 임금지급액", key="wage_prior")
            current_wages = money_input("당기 적격 상시근로자 임금지급액", key="wage_current")
            if headcount_growth == "증가하지 않음":
                eligible_wage = calculate_wage_increase_no_headcount_growth(prior_wages, current_wages)
                if current_wages < prior_wages:
                    warnings.append("임금액이 감소하여 임금증가 인정액을 0으로 처리했습니다.")
            else:
                hc1, hc2 = st.columns(2)
                with hc1:
                    prior_headcount = st.number_input(
                        "전기 상시근로자 수",
                        min_value=0.0,
                        value=0.0,
                        step=1.0,
                        key="headcount_prior",
                    )
                with hc2:
                    current_headcount = st.number_input(
                        "당기 상시근로자 수",
                        min_value=0.0,
                        value=0.0,
                        step=1.0,
                        key="headcount_current",
                    )
                avg_new_wage = money_input(
                    "당기 신규 상시근로자 1인당 평균 임금지급액",
                    key="wage_avg_new",
                )
                youth_addition = money_input(
                    "청년정규직근로자 임금증가 추가 인정액",
                    key="wage_youth",
                )
                converted_addition = money_input(
                    "정규직 전환 근로자 임금증가 추가 인정액",
                    key="wage_converted",
                )
                wage_details = calculate_wage_increase_with_headcount_growth(
                    prior_eligible_wages=prior_wages,
                    current_eligible_wages=current_wages,
                    prior_headcount=prior_headcount,
                    current_headcount=current_headcount,
                    average_wage_of_new_workers=avg_new_wage,
                    youth_regular_worker_wage_increase=youth_addition,
                    converted_regular_worker_wage_increase=converted_addition,
                    params=PARAMS,
                )
                eligible_wage = wage_details["recognized_wage_increase"]
                if current_headcount <= prior_headcount:
                    warnings.append("상시근로자 증가를 선택했지만 당기 인원이 전기 이하입니다.")
                if current_wages < prior_wages:
                    warnings.append("임금액이 감소하여 기본 임금증가액을 0으로 처리했습니다.")
                if wage_details["new_worker_component"] < wage_details["headcount_increase"] * avg_new_wage:
                    warnings.append("신규근로자 임금증가액이 전체 임금증가액 한도로 제한됐습니다.")
            render_amount_card("임금증가 인정액", eligible_wage)
            if wage_details:
                st.caption(
                    "기존근로자 구성액 " + fmt(wage_details["existing_worker_component"])
                    + " / 신규근로자 구성액 " + fmt(wage_details["new_worker_component"])
                )
            st.caption("상시근로자 범위와 청년·정규직 전환 요건은 사용자가 사전 검토한 값을 입력하는 간편 모듈입니다.")

    with cooperation_col:
        st.markdown("### 상생협력 지출")
        cooperation_spend = money_input(
            "세법상 요건을 충족한 실제 상생협력 지출액",
            key="cooperation_spend",
        )
        cooperation_recognized = cooperation_spend * PARAMS.cooperation_multiplier
        render_amount_card("환류 인정액", cooperation_recognized, "실제 지출액의 300%")
        st.caption("특수관계인 지원 등 제외요건을 검토한 실제 적격 지출액을 입력하세요.")

    if warnings:
        st.warning("\n".join(f"• {message}" for message in warnings))

returns = ReturnAmounts(
    investment=eligible_investment,
    dividend=eligible_dividend,
    wage_increase=eligible_wage,
    cooperation_actual_spend=cooperation_spend,
)

base_result = calculate_scenario(
    scenario_name="기준",
    corporate_income=base_income,
    returns=returns,
    due_prior_reserve=due_prior_reserve,
    carryforward_excess=carryforward_excess,
    requested_current_reserve=requested_current_reserve,
    params=PARAMS,
)


def method_label(method: str) -> str:
    return "투자포함형" if method == "investment_included" else "투자제외형"


def method_detail_df(result) -> pd.DataFrame:
    return pd.DataFrame(
        [
            ["기업소득", result.corporate_income],
            ["환류기준액", result.target_return],
            ["인정 환류액", result.recognized_return],
            ["당기 미환류소득", result.current_unreturned_income],
            ["당기 초과환류액", result.current_excess_return],
            ["기한도래 차기환류적립금", result.due_reserve_amount],
            ["당기 초과환류액으로 정산", result.due_reserve_offset_by_excess],
            ["기한도래 적립금 미정산액", result.due_reserve_shortfall],
            ["이월 초과환류액 사용", result.carryforward_excess_used],
            ["당기 차기환류적립금 사용", result.current_reserve_used],
            ["과세대상 당기 미환류소득", result.current_taxable_unreturned_income],
            ["당기분 추가 법인세", result.current_additional_tax],
            ["기한도래 적립금 추가 법인세", result.due_reserve_additional_tax],
            ["총 예상 추가 법인세", result.total_additional_tax],
            ["추가 환류 필요액", result.additional_return_needed],
            ["차기 이월 가능성 검토 대상 초과환류액", result.next_excess_pool_before_expiry_review],
        ],
        columns=["구분", f"금액({UNIT})"],
    )


def render_method(result) -> None:
    st.markdown(f"### {method_label(result.method)}")
    note = None
    if result.current_excess_return > 0:
        note = f"미환류소득은 0이며, 당기 초과환류액 {fmt(result.current_excess_return)}이 발생합니다."
    render_amount_card("당기 예상 미환류소득", result.current_unreturned_income, note)

    if result.current_reserve_requested > result.current_reserve_used + 1e-9:
        st.warning("요청한 당기 차기환류적립금이 당기 미환류소득 잔액보다 커서 실제 반영액을 자동으로 제한했습니다.")

    with st.expander("상세 계산 내역 보기"):
        st.dataframe(
            method_detail_df(result),
            hide_index=True,
            width="stretch",
            column_config={f"금액({UNIT})": st.column_config.NumberColumn(format="%.1f")},
        )


with result_tab:
    st.subheader("기준 기업소득 결과")
    left, right = st.columns(2)
    with left:
        render_method(base_result.investment_included)
    with right:
        render_method(base_result.investment_excluded)

    with st.expander("방식별 당기 인정 환류액"):
        c1, c2 = st.columns(2)
        with c1:
            render_amount_card(
                "투자포함형 당기 인정 환류액",
                base_result.investment_included.recognized_return,
                "기업소득 × 80%에서 차감되는 금액",
            )
        with c2:
            render_amount_card(
                "투자제외형 당기 인정 환류액",
                base_result.investment_excluded.recognized_return,
                "기업소득 × 30%에서 차감되는 금액",
            )
        st.caption(
            "투자포함형은 적격 투자액·배당액·임금증가 인정액·상생협력 인정액을 합산하고, "
            "투자제외형은 이 중 적격 투자액을 제외한 금액을 합산합니다."
        )


def scenario_card_html(name: str, income: float, result) -> str:
    safe_name = html.escape(name)
    a = result.investment_included
    b = result.investment_excluded
    a_note = f"<br><span class='small-note'>초과환류액 {fmt(a.current_excess_return)}</span>" if a.current_excess_return > 0 else ""
    b_note = f"<br><span class='small-note'>초과환류액 {fmt(b.current_excess_return)}</span>" if b.current_excess_return > 0 else ""
    return f"""
<div class="scenario-card">
  <div class="scenario-title">{safe_name}</div>
  <div class="scenario-row">
    <div class="scenario-label">예상 기업소득</div>
    <div class="scenario-number">{fmt(income)}</div>
  </div>
  <div class="scenario-row">
    <div class="scenario-label">투자포함형 당기 예상 미환류소득</div>
    <div class="scenario-number">{fmt(a.current_unreturned_income)}{a_note}</div>
  </div>
  <div class="scenario-row">
    <div class="scenario-label">투자제외형 당기 예상 미환류소득</div>
    <div class="scenario-number">{fmt(b.current_unreturned_income)}{b_note}</div>
  </div>
</div>
"""


with scenario_tab:
    st.subheader("기업소득 시나리오 비교")
    st.caption("기준 시나리오는 유지하고, 비교할 시나리오를 원하는 수만큼 직접 추가하세요.")

    scenario_count = int(
        st.number_input(
            "추가할 시나리오 수",
            min_value=0,
            max_value=8,
            value=0,
            step=1,
            key="scenario_count",
        )
    )

    scenario_pairs: list[tuple[str, float]] = [("기준", base_income)]
    for index in range(scenario_count):
        with st.container(border=True):
            st.markdown(f"#### 추가 시나리오 {index + 1}")
            name_col, income_col = st.columns([1, 1])
            with name_col:
                name = st.text_input(
                    "시나리오명",
                    value=f"시나리오 {index + 1}",
                    key=f"scenario_name_{index}",
                ).strip()
            with income_col:
                income = money_input(
                    "예상 기업소득",
                    key=f"scenario_income_{index}",
                    value=base_income,
                )
            if name:
                scenario_pairs.append((name, income))

    st.divider()
    st.markdown("### 시나리오별 핵심 결과")
    scenario_results = []
    for name, income in scenario_pairs:
        result = calculate_scenario(
            scenario_name=name,
            corporate_income=income,
            returns=returns,
            due_prior_reserve=due_prior_reserve,
            carryforward_excess=carryforward_excess,
            requested_current_reserve=requested_current_reserve,
            params=PARAMS,
        )
        scenario_results.append((name, income, result))

    for start in range(0, len(scenario_results), 3):
        row_items = scenario_results[start:start + 3]
        cols = st.columns(len(row_items))
        for col, (name, income, result) in zip(cols, row_items):
            with col:
                st.markdown(scenario_card_html(name, income, result), unsafe_allow_html=True)

with basis_tab:
    st.subheader("핵심 산식")
    st.code(
        """[투자포함형 A]
당기 산식 결과 = 기업소득 × 80% - 투자액 - 배당액 - 임금증가 인정액 - 상생협력 지출액 × 300%

[투자제외형 B]
당기 산식 결과 = 기업소득 × 30% - 배당액 - 임금증가 인정액 - 상생협력 지출액 × 300%

양수: 당기 미환류소득
음수: 초과환류액

당기분 과세대상 = 당기 미환류소득 - 사용한 이월 초과환류액 - 당기 새로 설정한 차기환류적립금
기한도래 적립금 추가납부 = max(기한도래 차기환류적립금 - 당기 초과환류액, 0) × 20%
""",
        language="text",
    )
    st.markdown(
        """
### 프로그램의 의도적 한계
- 적용대상 법인 여부와 기업소득 산정은 자동 판정하지 않습니다.
- 투자와 배당은 연간 합계에서 사용자가 입력한 제외항목을 차감하는 **잠정 계산**입니다.
- 임금 모듈은 세법상 적격 상시근로자·청년·정규직 전환 금액을 사용자가 사전 검토했다는 전제입니다.
- 이월 초과환류액은 발생연도별 소멸기한을 별도로 관리해야 합니다.
- 투자자산 처분에 따른 추징·이자상당액은 포함하지 않습니다.
- 실제 신고서 작성이나 세무의견을 대체하지 않습니다.
"""
    )
    st.markdown(
        """
### 법령 기준
- 「조세특례제한법」 제100조의32
- 「조세특례제한법 시행령」 제100조의32
- 기준일: 2026-07-20
"""
    )
