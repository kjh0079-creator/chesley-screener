"""
체슬리 탑엔드식 턴어라운드 5단계 퀀트 스크리너 엔진
"""

import yfinance as yf
import pandas as pd
import numpy as np


REVENUE_GROWTH_MIN = 20.0


def _finite_number(value):
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if np.isfinite(number) else None


def _sort_quarterly_statement(statement):
    """Normalize period ends and sort newest first; ambiguous dates are unusable."""
    if statement is None or statement.empty:
        return pd.DataFrame()
    # Numeric column labels are not reporting dates.
    if any(isinstance(col, (int, float, np.number)) for col in statement.columns):
        return pd.DataFrame()
    dates = pd.to_datetime(statement.columns, errors="coerce", utc=True, format="mixed")
    dates = dates.tz_convert(None).normalize()
    if dates.isna().any() or dates.duplicated().any():
        return pd.DataFrame()
    ordered = statement.copy()
    ordered.columns = dates
    return ordered.sort_index(axis=1, ascending=False)


def calculate_revenue_growth_yoy(quarterly_financials):
    """Latest quarterly revenue versus the same period one year earlier.

    Match period ends, never column positions. A seven-day tolerance accommodates
    52/53-week fiscal calendars. Missing/ambiguous periods or invalid revenue
    produce None, not an assumed growth rate or a fallback to an older quarter.
    """
    result = {
        "rev_growth_yoy": None,
        "revenue_period": None,
        "revenue_prior_year_period": None,
        "revenue_current": None,
        "revenue_prior_year": None,
        "rev_growth_reason": None,
    }
    fin = _sort_quarterly_statement(quarterly_financials)
    if fin.empty:
        result["rev_growth_reason"] = "분기 재무제표 또는 유효한 결산일 부족"
        return result
    latest = fin.columns[0]
    result["revenue_period"] = latest.date().isoformat()
    if "Total Revenue" not in fin.index or fin.index.duplicated().any():
        result["rev_growth_reason"] = "매출 항목 누락 또는 중복 재무 항목"
        return result
    result["revenue_current"] = _finite_number(fin.at["Total Revenue", latest])
    target = latest - pd.DateOffset(years=1)
    candidates = [date for date in fin.columns
                  if date < latest and abs(date - target) <= pd.Timedelta(days=7)]
    if len(candidates) != 1:
        result["rev_growth_reason"] = "전년 동기 분기 누락 또는 비교 결산일 중복"
        return result
    prior = candidates[0]
    result["revenue_prior_year_period"] = prior.date().isoformat()
    result["revenue_prior_year"] = _finite_number(fin.at["Total Revenue", prior])
    current, previous = result["revenue_current"], result["revenue_prior_year"]
    if current is None or current < 0:
        result["rev_growth_reason"] = "최신 분기 매출 누락·비유한 값 또는 음수"
        return result
    if previous is None or previous <= 0:
        result["rev_growth_reason"] = "전년 동기 매출 누락·비유한 값 또는 0 이하"
        return result
    growth = _finite_number((current - previous) / previous * 100)
    if growth is None:
        result["rev_growth_reason"] = "매출 성장률 계산 결과가 유효하지 않음"
        return result
    result["rev_growth_yoy"] = growth
    return result


def passes_revenue_growth(rev_growth, minimum=REVENUE_GROWTH_MIN):
    """Use the unrounded YoY value for all growth eligibility decisions."""
    growth = _finite_number(rev_growth)
    return growth is not None and growth >= minimum


def calculate_canslim_score(ticker_info, rev_growth, op_income, ebitda, ocf):
    """
    CANSLIM 모형 기반 점수화 (100점 만점)
    - C (Current Earnings/Revenue): 최근 분기 성장률 (25점)
    - A (Annual Earnings): 연간 지속성 및 마진 (20점)
    - N (New Catalyst): 신제품/기술/시대 부합성 (15점)
    - S (Supply/Demand): 시총 및 거래대금 유동성 (15점)
    - L (Leader/RS): 52주 신고가 근접도 및 상대강도 (15점)
    - I/M (Institutional/Market): 기관 보유 및 현금흐름 건전성 (10점)
    """
    # A complete CANSLIM score cannot be calculated without verified YoY.
    rev_growth = _finite_number(rev_growth)
    if rev_growth is None:
        return None
    score = 0.0

    # C: 최근 분기 매출 성장률 (최대 25점)
    if rev_growth >= 30:
        score += 25
    elif rev_growth >= 20:
        score += 20
    elif rev_growth >= 10:
        score += 15
    else:
        score += max(0, rev_growth)

    # A: EBITDA / OCF 흑자 여부 (최대 20점)
    if ebitda > 0 and ocf > 0:
        score += 20
    elif ebitda > 0 or ocf > 0:
        score += 14
    else:
        score += 5

    # S: 시총 적정성 $500M ~ $20B (최대 15점)
    market_cap = ticker_info.get("marketCap", 0)
    if 500_000_000 <= market_cap <= 20_000_000_000:
        score += 15
    elif market_cap > 20_000_000_000:
        score += 10
    else:
        score += 5

    # L: 52주 고가 대비 현재 위치 (최대 15점)
    fifty_two_high = ticker_info.get("fiftyTwoWeekHigh", 0)
    current_price = ticker_info.get("currentPrice") or ticker_info.get("regularMarketPrice", 0)
    if fifty_two_high > 0 and current_price > 0:
        drawdown = (current_price - fifty_two_high) / fifty_two_high
        if drawdown >= -0.10:  # 고가 대비 -10% 이내 (강한 모멘텀)
            score += 15
        elif drawdown >= -0.25:
            score += 12
        elif drawdown >= -0.40:
            score += 9
        else:
            score += 5
    else:
        score += 8

    # N & I/M: 기본 보정 (최대 25점)
    inst_own = ticker_info.get("heldPercentInstitutions", 0) or 0.5
    score += min(15, inst_own * 20)
    score += 10  # 시대적 촉매 기본 점수

    return round(min(95.0, max(25.0, score)), 1)


def estimate_quarters_to_breakeven(hist_op_losses):
    """
    적자 축소 추세를 바탕으로 GAAP 영업이익 흑자전환 분기(t) 추정 (외삽 알고리즘)
    """
    if len(hist_op_losses) < 2:
        return 6  # 기본값

    # 최근 손실
    latest_loss = hist_op_losses[0]
    if latest_loss >= 0:
        return 0  # 이미 흑자

    # 직전 분기들과의 평균 개선 속도 (단위: $M)
    improvements = []
    for i in range(len(hist_op_losses) - 1):
        # i=0(최근), i+1(이전)
        diff = hist_op_losses[i] - hist_op_losses[i + 1]  # 개선 폭 (+이면 적자 축소)
        improvements.append(diff)

    avg_improvement = np.mean(improvements) if improvements else 0

    if avg_improvement <= 0:
        return 12  # 적자 폭 확대 중 (흑전 멀거나 불가)

    # 흑자 전환까지 남은 분기
    quarters = abs(latest_loss) / avg_improvement
    return int(np.clip(np.ceil(quarters), 1, 16))


def analyze_live_ticker(ticker_symbol):
    """
    단일 종목 실시간 yfinance 재무 분석 및 5단계 필터 판정
    """
    stock = yf.Ticker(ticker_symbol)
    info = stock.info

    if not info or "shortName" not in info:
        return None

    # 시총 ($B)
    market_cap = info.get("marketCap", 0)
    market_cap_b = market_cap / 1e9 if market_cap else 0.0

    # 재무제표
    fin = _sort_quarterly_statement(stock.quarterly_financials)
    cf = _sort_quarterly_statement(stock.quarterly_cashflow)

    if fin is None or fin.empty or cf is None or cf.empty:
        return None

    # 최근 분기 데이터
    latest_fin = fin.iloc[:, 0]

    latest_cf = cf.iloc[:, 0]

    # 매출 및 성장률
    revenue = calculate_revenue_growth_yoy(fin)
    rev_now = revenue["revenue_current"]
    rev_growth = revenue["rev_growth_yoy"]
    revenue_growth_pass = passes_revenue_growth(rev_growth)

    # 손익 지표
    op_income = latest_fin.get("Operating Income", 0) or 0
    ebitda = latest_fin.get("EBITDA", info.get("ebitda", 0)) or 0
    ocf = latest_cf.get("Operating Cash Flow", 0) or 0
    sbc = latest_cf.get("Stock Based Compensation", 0) or 0

    sbc_ratio = (sbc / rev_now * 100) if rev_now is not None and rev_now > 0 else 0.0

    # 흑전 추정 분기
    losses = []
    for col in fin.columns[:4]:
        losses.append(fin[col].get("Operating Income", 0) / 1e6)
    est_quarters = estimate_quarters_to_breakeven(losses)

    # CANSLIM 점수 계산
    canslim = calculate_canslim_score(info, rev_growth, op_income, ebitda, ocf)

    # 파트 2 통과 여부 판정
    # 조건: 시총 0.5B~20B, 매출성장 >= 20%, GAAP적자(<0), EBITDA>0 또는 OCF>0, 8분기 내 흑전
    pass_part2 = (
        (0.5 <= market_cap_b <= 20.0) and
        revenue_growth_pass and
        (op_income < 0) and
        (ebitda > 0 or ocf > 0) and
        (est_quarters <= 8)
    )

    return {
        "ticker": ticker_symbol.upper(),
        "name": info.get("shortName", ticker_symbol),
        "sector": info.get("sector", "기타"),
        "market_cap_b": round(market_cap_b, 2),
        **revenue,
        "revenue_growth_pass": revenue_growth_pass,
        "op_income_m": round(op_income / 1e6, 1),
        "ebitda_m": round(ebitda / 1e6, 1),
        "ocf_m": round(ocf / 1e6, 1),
        "ebitda_positive": bool(ebitda > 0),
        "ocf_positive": bool(ocf > 0),
        "sbc_ratio": round(sbc_ratio, 1),
        "est_quarters_to_gaap": est_quarters,
        "canslim": canslim,
        "pass_part2": bool(pass_part2),
        "summary": info.get("longBusinessSummary", "")[:120] + "..." if info.get("longBusinessSummary") else "사업 개요 정보 없음",
        "current_price": info.get("currentPrice") or info.get("regularMarketPrice", 0)
    }
