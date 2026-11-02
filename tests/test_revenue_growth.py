"""Offline regression tests: synthetic financials, never investment data."""
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

import screener_engine as engine


def make_stock(current=120e6, previous=100e6, prior_year=100e6):
    dates = pd.to_datetime(["2026-09-30", "2026-06-30", "2026-03-31",
                            "2025-12-31", "2025-09-30"])
    fin = pd.DataFrame([
        [current, previous, 100e6, 100e6, prior_year],
        [-10e6, -15e6, -20e6, -25e6, -30e6],
        [5e6, 4e6, 3e6, 2e6, 1e6],
    ], index=["Total Revenue", "Operating Income", "EBITDA"], columns=dates)
    cf = pd.DataFrame([[8e6], [1e6]],
                      index=["Operating Cash Flow", "Stock Based Compensation"],
                      columns=[dates[0]])
    return SimpleNamespace(
        info={"shortName": "Synthetic fixture", "marketCap": 2e9,
              "currentPrice": 80, "fiftyTwoWeekHigh": 100,
              "heldPercentInstitutions": 0.5},
        quarterly_financials=fin, quarterly_cashflow=cf,
    )


def analyze(stock):
    with patch.object(engine.yf, "Ticker", return_value=stock):
        return engine.analyze_live_ticker("TEST")


def test_yoy_not_qoq_and_full_precision():
    stock = make_stock(current=130e6, previous=200e6, prior_year=100e6)
    result = analyze(stock)
    assert result["rev_growth_yoy"] == pytest.approx(30)
    assert result["revenue_growth_pass"] is True
    assert result["pass_part2"] is True
    assert result["canslim"] == 92
    assert result["revenue_period"] == "2026-09-30"
    assert result["revenue_prior_year_period"] == "2025-09-30"
    # The old QoQ calculation would reject this stock: -35%.
    assert (130e6 - 200e6) / 200e6 * 100 == -35


def test_qoq_false_positive_is_rejected():
    result = analyze(make_stock(current=130e6, previous=100e6, prior_year=125e6))
    assert result["rev_growth_yoy"] == pytest.approx(4)
    assert result["revenue_growth_pass"] is False
    assert result["pass_part2"] is False
    assert result["canslim"] == 71
    # Old QoQ was +30%, with a 92-point score and a passing decision.


@pytest.mark.parametrize("growth,passes,score", [
    (19.96, False, 82), (20, True, 87), (20.01, True, 87),
    (29.96, True, 87), (30, True, 92), (-10, False, 67),
])
def test_thresholds_use_unrounded_yoy(growth, passes, score):
    result = analyze(make_stock(current=100e6 * (1 + growth / 100)))
    assert result["rev_growth_yoy"] == pytest.approx(growth)
    assert result["revenue_growth_pass"] is passes
    assert result["pass_part2"] is passes
    assert result["canslim"] == score


@pytest.mark.parametrize("bad", [None, np.nan, np.inf, -np.inf, 0, -1, "bad", pd.NA])
def test_invalid_prior_year_never_assumed_or_scored(bad):
    result = analyze(make_stock(prior_year=bad))
    assert result["rev_growth_yoy"] is None
    assert result["rev_growth_reason"]
    assert result["revenue_growth_pass"] is False
    assert result["pass_part2"] is False
    assert result["canslim"] is None


@pytest.mark.parametrize("bad", [None, np.nan, np.inf, -np.inf, -1, "bad", pd.NA])
def test_invalid_latest_does_not_use_older_quarter(bad):
    result = analyze(make_stock(current=bad))
    assert result["rev_growth_yoy"] is None
    assert result["pass_part2"] is False
    assert result["canslim"] is None


def test_zero_current_revenue_is_valid_negative_100_percent():
    result = analyze(make_stock(current=0))
    assert result["rev_growth_yoy"] == -100
    assert result["canslim"] == 67
    assert result["pass_part2"] is False


@pytest.mark.parametrize("count", [1, 2, 4])
def test_missing_prior_year_with_short_history(count):
    stock = make_stock()
    stock.quarterly_financials = stock.quarterly_financials.iloc[:, :count]
    result = analyze(stock)
    assert result["rev_growth_yoy"] is None
    assert result["canslim"] is None
    assert result["pass_part2"] is False


def test_missing_intermediate_quarters_still_matches_dates():
    stock = make_stock()
    stock.quarterly_financials = stock.quarterly_financials.iloc[:, [0, 4]]
    assert analyze(stock)["rev_growth_yoy"] == 20


@pytest.mark.parametrize("previous", [0, None, np.nan])
def test_previous_quarter_revenue_does_not_replace_yoy(previous):
    result = analyze(make_stock(previous=previous))
    assert result["rev_growth_yoy"] == 20
    assert result["pass_part2"] is True


def test_unsorted_statements_keep_latest_period_and_loss_trend():
    stock = make_stock()
    expected = analyze(stock)
    stock.quarterly_financials = stock.quarterly_financials.iloc[:, [4, 1, 3, 0, 2]]
    stock.quarterly_cashflow[pd.Timestamp("2026-06-30")] = [-1e6, 2e6]
    stock.quarterly_cashflow = stock.quarterly_cashflow.iloc[:, ::-1]
    assert analyze(stock) == expected


@pytest.mark.parametrize("latest,prior", [
    ("2026-01-31", "2025-01-31"),  # non-calendar fiscal year
    ("2026-02-07", "2025-02-01"),  # 53-week fiscal calendar
    ("2024-02-29", "2023-02-28"),  # leap year
    ("2026-09-30", "2025-09-23"),  # exact tolerance boundary
])
def test_fiscal_calendars(latest, prior):
    fin = pd.DataFrame([[120, 100]], index=["Total Revenue"],
                       columns=pd.to_datetime([latest, prior]))
    result = engine.calculate_revenue_growth_yoy(fin)
    assert result["rev_growth_yoy"] == 20
    assert result["revenue_prior_year_period"] == prior


@pytest.mark.parametrize("prior", ["2025-09-22", "2025-06-30", "2024-09-30"])
def test_wrong_comparison_period_is_not_substituted(prior):
    fin = pd.DataFrame([[120, 100]], index=["Total Revenue"],
                       columns=pd.to_datetime(["2026-09-30", prior]))
    assert engine.calculate_revenue_growth_yoy(fin)["rev_growth_yoy"] is None


def test_ambiguous_comparison_period_is_rejected():
    fin = pd.DataFrame([[120, 100, 90]], index=["Total Revenue"],
                       columns=pd.to_datetime(["2026-09-30", "2025-09-30", "2025-09-29"]))
    assert engine.calculate_revenue_growth_yoy(fin)["rev_growth_yoy"] is None


@pytest.mark.parametrize("columns", [
    ["bad", "2025-09-30"], [0, 1],
    ["2026-09-30", "2026-09-30"],
])
def test_invalid_or_duplicate_reporting_dates(columns):
    fin = pd.DataFrame([[120, 100]], index=["Total Revenue"], columns=columns)
    assert engine.calculate_revenue_growth_yoy(fin)["rev_growth_yoy"] is None


def test_missing_revenue_row():
    stock = make_stock()
    stock.quarterly_financials = stock.quarterly_financials.drop("Total Revenue")
    result = analyze(stock)
    assert result["rev_growth_yoy"] is None
    assert result["canslim"] is None
    assert result["pass_part2"] is False


@pytest.mark.parametrize("growth", [None, np.nan, np.inf, -np.inf])
def test_score_and_filter_reject_nonfinite_growth(growth):
    assert engine.calculate_canslim_score({}, growth, 0, 0, 0) is None
    assert engine.passes_revenue_growth(growth) is False


@pytest.mark.parametrize("ticker", [
    "AEHR", "U", "FSLY", "STLN", "XMTR", "NTRA", "GKOS", "RBRK", "BRZE",
    "SNOW", "IRTC", "QXO", "BKSY", "MP", "CSTL", "TE", "ASTS", "PL",
    "EVLV", "RBLX", "LASR", "TTAN",
])
def test_captured_existing_ticker_result(ticker):
    import json
    from pathlib import Path
    from tools.audit_revenue_growth import restore_frame

    folder = Path(__file__).resolve().parents[1] / "docs/revenue-audit-20261102"
    snapshots = json.loads((folder / "snapshots.json").read_text())["snapshots"]
    snapshot = next(s for s in snapshots if s["ticker"] == ticker)
    expected = pd.read_csv(folder / "comparison.csv").set_index("ticker").loc[ticker]
    result = analyze(SimpleNamespace(
        info=snapshot["info"],
        quarterly_financials=restore_frame(snapshot["financials"]),
        quarterly_cashflow=restore_frame(snapshot["cashflow"]),
    ))
    assert result["rev_growth_yoy"] == pytest.approx(expected["new_yoy"])
    assert result["canslim"] == expected["new_canslim"]
    assert result["revenue_growth_pass"] == expected["new_growth_pass"]
    assert result["pass_part2"] == expected["new_part2_pass"]


def test_other_part2_conditions_are_preserved():
    stock = make_stock()
    stock.info["marketCap"] = 100e9
    assert analyze(stock)["pass_part2"] is False
    stock.info["marketCap"] = 2e9
    stock.quarterly_financials.loc["Operating Income", :] = 1e6
    assert analyze(stock)["pass_part2"] is False


@pytest.mark.parametrize("current,prior,display,decision,score", [
    (130e6, 125e6, "+4.00%", "미달", "71.0점"),
    (119.96e6, 100e6, "+19.96%", "미달", "82.0점"),
    (120e6, 100e6, "+20.00%", "20% 이상 합격", "87.0점"),
    (90e6, 100e6, "-10.00%", "미달", "67.0점"),
    (130e6, 0, "확인 불가", "데이터 부족·비교 불가", "산정 불가"),
])
def test_streamlit_uses_engine_growth_score_and_decision(current, prior, display, decision, score):
    from pathlib import Path
    from streamlit.testing.v1 import AppTest

    with patch.object(engine.yf, "Ticker", return_value=make_stock(current=current, prior_year=prior)):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"))
        app.run(timeout=30)
    assert not app.exception
    metric = next(m for m in app.metric if m.label == "매출 성장률 (YoY)")
    assert metric.value == display
    assert metric.delta == decision
    text = "\n".join(m.value for m in app.markdown)
    assert score in text
    if prior == 0:
        assert "통과 보류" in text
        assert any("성장률 조건과 최종 통과를 인정하지" in w.value for w in app.warning)

