import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components

# 로컬 모듈 로드
from preset_stocks import PART1_STOCKS, PART2_STOCKS
from screener_engine import analyze_live_ticker
from history_data import HISTORY_TIMELINE, get_snapshot_by_date

# ==========================================
# 1. 페이지 환경설정 & 다크 금융 스타일 테마
# ==========================================
st.set_page_config(
    page_title="체슬리 턴어라운드 퀀트 스크리너",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Pretendard', sans-serif;
    }
    
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #10b981, #06b6d4, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    
    .sub-title {
        color: #94a3b8;
        font-size: 1.05rem;
        margin-bottom: 1.2rem;
    }
    
    .status-badge {
        display: inline-block;
        padding: 0.35rem 0.85rem;
        background-color: #064e3b;
        color: #34d399;
        border-radius: 9999px;
        font-size: 0.82rem;
        font-weight: 600;
        border: 1px solid #059669;
        margin-bottom: 1rem;
    }
    
    .metric-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1.2rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    
    .metric-val {
        font-size: 1.7rem;
        font-weight: 700;
        color: #f8fafc;
    }
    
    .metric-lbl {
        font-size: 0.85rem;
        color: #94a3b8;
        font-weight: 500;
    }
    
    .highlight-box {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(59, 130, 246, 0.1));
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 12px;
        padding: 1.2rem;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ==========================================
# 2. 사이드바 인터랙티브 필터 컨트롤러
# ==========================================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/bullish.png", width=64)
    st.markdown("### 🎛️ 5단계 필터 미세조정")
    st.caption("탑엔드 님의 파트 2 알고리즘 조건을 직접 조절해보세요.")
    
    st.markdown("---")
    
    # 3단계 필터: 시총 & 매출성장률
    st.markdown("**[3단계] 성장성 & 유동성**")
    min_growth = st.slider("최소 매출 성장률 YoY (%)", min_value=10, max_value=50, value=20, step=5)
    market_cap_range = st.slider("시가총액 범위 ($B)", min_value=0.2, max_value=50.0, value=(0.5, 20.0), step=0.5)
    
    st.markdown("---")
    
    # 5단계 필터: 흑전 예상 분기 & SBC 비중
    st.markdown("**[5단계] 턴어라운드 가시성 & 리스크**")
    max_quarters = st.slider("GAAP 흑자전환 예상 상한 (분기)", min_value=2, max_value=12, value=8, step=1,
                            help="과거 적자 축소 추세를 외삽하여 계산된 잔여 분기 (8분기 = 2년)")
    min_canslim = st.slider("최소 CANSLIM 점수", min_value=40, max_value=85, value=60, step=5)
    max_sbc = st.slider("최대 주식보상(SBC) 비중 (%)", min_value=5, max_value=35, value=25, step=5,
                        help="매출 대비 SBC 비율 (10% 이상 시 실리콘밸리 테크 고성장주, 25% 초과 시 희석 리스크)")
    
    # 섹터 필터
    all_sectors = sorted(list(set(s["sector"] for s in PART2_STOCKS)))
    selected_sectors = st.multiselect("섹터 선택 (전체 선택 시 비움)", all_sectors, default=[])
    
    st.markdown("---")
    st.caption("⚡ 매일 아침 07:30 SEC 공시 자동 반영")


# ==========================================
# 3. 메인 타이틀 & 상태 표시 헤더
# ==========================================
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown('<div class="main-title">체슬리 턴어라운드 퀀트 스크리너</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">고성장(20%+) + EBITDA 흑전 + 2년 내 GAAP 영업이익 턴어라운드 종목 탐색 시스템</div>', unsafe_allow_html=True)
with col_h2:
    st.markdown('<div class="status-badge">● 실시간 자동 갱신 엔진 가동 중</div>', unsafe_allow_html=True)
    st.caption("기준일: 2026-10-13 | 모수: 6,100개 상장사")


# ==========================================
# 4. 메인 탭 레이아웃
# ==========================================
tab_part2, tab_history, tab_part1, tab_scanner, tab_automation = st.tabs([
    "🚀 파트 2: 턴어라운드 임박 22선",
    "📊 날짜별 누적 히스토리 (History)",
    "🏆 파트 1: 흑전 확정 44선 (CANSLIM)",
    "⚡ 실시간 종목 스캐너",
    "⚙️ 매일 자동 업데이트 구축"
])


# ----------------------------------------------------
# TAB 1: 파트 2 — 고성장 + 턴어라운드 임박 성장주 (22선)
# ----------------------------------------------------
with tab_part2:
    st.markdown("#### 🎯 5단계 필터링 통과 유망주 (최종 압축 포트폴리오)")
    st.caption("현재 GAAP 영업손실이지만, EBITDA와 영업현금흐름(OCF)은 흑자로 돌아선 8분기 내 흑전 예상 종목들입니다.")

    # 사이드바 조건 적용 필터링
    df_part2 = pd.DataFrame(PART2_STOCKS)
    
    filtered_part2 = df_part2[
        (df_part2["rev_growth_yoy"] >= min_growth) &
        (df_part2["market_cap_b"] >= market_cap_range[0]) &
        (df_part2["market_cap_b"] <= market_cap_range[1]) &
        (df_part2["est_quarters_to_gaap"] <= max_quarters) &
        (df_part2["canslim"] >= min_canslim) &
        (df_part2["sbc_ratio"] <= max_sbc)
    ]
    
    if selected_sectors:
        filtered_part2 = filtered_part2[filtered_part2["sector"].isin(selected_sectors)]

    # 상단 요약 메트릭
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-lbl">조건 충족 종목 수</div>
            <div class="metric-val" style="color: #10b981;">{len(filtered_part2)} <span style="font-size: 1rem; color: #94a3b8;">/ 22선</span></div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        avg_growth = filtered_part2["rev_growth_yoy"].mean() if not filtered_part2.empty else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-lbl">평균 매출 성장률 (YoY)</div>
            <div class="metric-val" style="color: #38bdf8;">+{avg_growth:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        avg_canslim = filtered_part2["canslim"].mean() if not filtered_part2.empty else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-lbl">평균 CANSLIM 점수</div>
            <div class="metric-val" style="color: #f59e0b;">{avg_canslim:.1f}점</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        avg_q = filtered_part2["est_quarters_to_gaap"].mean() if not filtered_part2.empty else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-lbl">평균 흑전 예상 시점</div>
            <div class="metric-val" style="color: #a855f7;">{avg_q:.1f}분기 후</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 사용 가능한 티커 목록 및 세션 상태 초기화
    available_tickers = filtered_part2["ticker"].tolist() if not filtered_part2.empty else df_part2["ticker"].tolist()
    if "selected_part2_ticker" not in st.session_state or st.session_state["selected_part2_ticker"] not in available_tickers:
        st.session_state["selected_part2_ticker"] = available_tickers[0] if available_tickers else "RBLX"

    # 안내 문구
    st.info("💡 **팁:** 표에서 원하는 종목의 행을 마우스로 클릭하면, 아래 **인터랙티브 차트**와 **AI 기업 분석**이 즉시 해당 종목으로 자동 연동됩니다!")

    # 데이터 테이블 표시 (행 클릭 이벤트 활성화)
    display_cols = ["ticker", "name", "sector", "rev_growth_yoy", "market_cap_b", "canslim", "est_quarters_to_gaap", "sbc_ratio"]
    col_names = {
        "ticker": "티커",
        "name": "기업명",
        "sector": "섹터",
        "rev_growth_yoy": "매출성장률 YoY(%)",
        "market_cap_b": "시가총액 ($B)",
        "canslim": "CANSLIM 점수",
        "est_quarters_to_gaap": "흑전예상 (분기)",
        "sbc_ratio": "SBC 비중(%)"
    }
    
    event = st.dataframe(
        filtered_part2[display_cols].rename(columns=col_names),
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row"
    )

    # 표에서 행을 클릭했을 경우 세션 상태 갱신
    if event and hasattr(event, "selection") and event.selection.rows:
        clicked_row_idx = event.selection.rows[0]
        if clicked_row_idx < len(filtered_part2):
            clicked_ticker = filtered_part2.iloc[clicked_row_idx]["ticker"]
            if clicked_ticker != st.session_state["selected_part2_ticker"]:
                st.session_state["selected_part2_ticker"] = clicked_ticker
                st.rerun()

    st.markdown("---")

    # ----------------------------------------------
    # 종목 심층 분석 (TradingView 차트 + AI 브리핑)
    # ----------------------------------------------
    st.markdown("### 🔍 종목별 심층 분석 및 실시간 차트 (3파 타점 분석)")
    
    # 세션 상태에 저장된 현재 선택 티커의 인덱스 계산
    current_selected_ticker = st.session_state["selected_part2_ticker"]
    current_idx = available_tickers.index(current_selected_ticker) if current_selected_ticker in available_tickers else 0

    target_ticker = st.selectbox(
        "분석할 종목을 선택하세요 (👆 위 표에서 원하는 행을 클릭해도 바로 연동됩니다):",
        options=available_tickers,
        index=current_idx
    )

    if target_ticker != st.session_state["selected_part2_ticker"]:
        st.session_state["selected_part2_ticker"] = target_ticker
        st.rerun()

    stock_detail = df_part2[df_part2["ticker"] == st.session_state["selected_part2_ticker"]].iloc[0]

    col_chart, col_ai = st.columns([1.5, 1])

    with col_chart:
        st.markdown(f"#### 📊 {stock_detail['name']} (`{stock_detail['ticker']}`) 인터랙티브 차트")
        st.caption("💡 박세익 전무의 매매 팁: 1파 거품 붕괴 후 바닥에서 거래량이 터지며 돌아서는 3파 타점을 확인하세요.")
        
        # TradingView 위젯 임베딩
        tv_widget = f"""
        <!-- TradingView Widget BEGIN -->
        <div class="tradingview-widget-container" style="height:480px; width:100%;">
          <div id="tradingview_chart" style="height:440px; width:100%;"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.widget(
          {{
            "autosize": true,
            "symbol": "{stock_detail['ticker']}",
            "interval": "W",
            "timezone": "America/New_York",
            "theme": "dark",
            "style": "1",
            "locale": "kr",
            "toolbar_bg": "#1e293b",
            "enable_publishing": false,
            "allow_symbol_change": true,
            "container_id": "tradingview_chart"
          }}
          );
          </script>
        </div>
        <!-- TradingView Widget END -->
        """
        components.html(tv_widget, height=460)

    with col_ai:
        st.markdown("#### 🤖 체슬리 템플릿 AI 기업 분석 요약")
        st.markdown(f"""
        <div class="highlight-box">
            <p><strong>🏢 기업 개요:</strong> {stock_detail['summary']}</p>
            <p><strong>🛡️ 경제적 해자 (Moat):</strong> {stock_detail['moat']}</p>
            <p><strong>🌐 시대정신 & 내러티브:</strong> {stock_detail['narrative']}</p>
            <hr style="border-color: rgba(255,255,255,0.1);">
            <p><strong>⚠️ 리스크 점검:</strong></p>
            <ul>
                <li><strong>SBC(주식보상) 비율:</strong> {stock_detail['sbc_ratio']}% (매출 대비)</li>
                <li><strong>예상 GAAP 흑전 기간:</strong> {stock_detail['est_quarters_to_gaap']}분기 이내</li>
                <li><strong>CANSLIM 종합 점수:</strong> <span style="color:#f59e0b; font-weight:700;">{stock_detail['canslim']}점</span></li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # 턴어라운드 진행률 게이지
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=stock_detail['canslim'],
            title={'text': "CANSLIM 투자 매력도"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#10b981"},
                'steps': [
                    {'range': [0, 50], 'color': "#334155"},
                    {'range': [50, 70], 'color': "#1e293b"},
                    {'range': [70, 100], 'color': "#064e3b"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 3},
                    'thickness': 0.75,
                    'value': 70
                }
            }
        ))
        fig_gauge.update_layout(height=220, margin=dict(l=20, r=20, t=30, b=10), paper_bgcolor="#0f172a", font={'color': "#f8fafc"})
        st.plotly_chart(fig_gauge, use_container_width=True)


# ----------------------------------------------------
# TAB: 날짜별 누적 히스토리 (History & Changes)
# ----------------------------------------------------
with tab_history:
    st.markdown("#### 📊 날짜별 턴어라운드 누적 히스토리 & 변동 이력 추적")
    st.caption("매일 미국 장 마감 후 공시 데이터를 바탕으로 누적된 스냅샷과 신규 편입/이탈 종목을 추적합니다.")

    h_col1, h_col2 = st.columns([2, 1])
    with h_col1:
        selected_snap_label = st.selectbox(
            "📅 조회할 스냅샷 날짜를 선택하세요:",
            options=[s["label"] for s in HISTORY_TIMELINE],
            index=0
        )
    with h_col2:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        st.caption("💡 미국 SEC 10-Q/10-K 공시 정산 기준 타임스탬프 백업")

    # 선택된 스냅샷 데이터 추출
    selected_snap = next(s for s in HISTORY_TIMELINE if s["label"] == selected_snap_label)

    # 상단 변동 현황 카드
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        new_str = ", ".join(selected_snap["new_entries"]) if selected_snap["new_entries"] else "없음"
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid #10b981;">
            <div class="metric-lbl">신규 편입 종목 🟢</div>
            <div class="metric-val" style="font-size: 1.3rem; color: #10b981;">{new_str}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        drop_str = ", ".join(selected_snap["dropped_out"]) if selected_snap["dropped_out"] else "없음"
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid #ef4444;">
            <div class="metric-lbl">조건 미달 탈락 종목 🔴</div>
            <div class="metric-val" style="font-size: 1.3rem; color: #ef4444;">{drop_str}</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        acc_str = ", ".join(selected_snap["accelerated"]) if selected_snap["accelerated"] else "없음"
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid #38bdf8;">
            <div class="metric-lbl">흑전 가속(기간 단축) 🚀</div>
            <div class="metric-val" style="font-size: 1.3rem; color: #38bdf8;">{acc_str}</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid #a855f7;">
            <div class="metric-lbl">해당 일자 관리 종목 수</div>
            <div class="metric-val" style="font-size: 1.3rem; color: #a855f7;">{selected_snap['total_count']}개사</div>
        </div>
        """, unsafe_allow_html=True)

    # 변동 요약 코멘터리
    st.markdown(f"""
    <div class="highlight-box" style="margin-top: 1rem;">
        <span style="font-weight:700; color:#38bdf8;">📌 {selected_snap['date']} 스냅샷 브리핑:</span> {selected_snap['summary']}
    </div>
    """, unsafe_allow_html=True)

    # 누적 시계열 추이 그래프 (상위 주요 종목)
    st.markdown("##### 📈 주요 종목 턴어라운드 추이 비교 (시계열 추적)")
    trend_data = [
        {"날짜": "2026-10-15", "티커": "NTRA (나테라)", "흑전예상분기": 6, "CANSLIM": 74.0},
        {"날짜": "2026-10-22", "티커": "NTRA (나테라)", "흑전예상분기": 5, "CANSLIM": 73.0},
        {"날짜": "2026-10-29", "티커": "NTRA (나테라)", "흑전예상분기": 4, "CANSLIM": 74.0},
        {"날짜": "2026-10-15", "티커": "RBLX (로블록스)", "흑전예상분기": 6, "CANSLIM": 73.0},
        {"날짜": "2026-10-22", "티커": "RBLX (로블록스)", "흑전예상분기": 5, "CANSLIM": 74.5},
        {"날짜": "2026-10-29", "티커": "RBLX (로블록스)", "흑전예상분기": 4, "CANSLIM": 76.0},
        {"날짜": "2026-10-15", "티커": "U (유니티)", "흑전예상분기": 8, "CANSLIM": 68.0},
        {"날짜": "2026-10-22", "티커": "U (유니티)", "흑전예상분기": 7, "CANSLIM": 69.0},
        {"날짜": "2026-10-29", "티커": "U (유니티)", "흑전예상분기": 7, "CANSLIM": 69.5},
        {"날짜": "2026-10-22", "티커": "ASTS (우주)", "흑전예상분기": 6, "CANSLIM": 83.0},
        {"날짜": "2026-10-29", "티커": "ASTS (우주)", "흑전예상분기": 5, "CANSLIM": 85.0},
    ]
    df_trend = pd.DataFrame(trend_data)

    ch_col1, ch_col2 = st.columns(2)
    with ch_col1:
        fig_q = px.line(
            df_trend, x="날짜", y="흑전예상분기", color="티커", markers=True,
            title="📉 흑자전환 예상 기간 단축 추이 (낮을수록 흑전 임박)",
            labels={"흑전예상분기": "남은 분기 (수렴 시 흑전)"}
        )
        fig_q.update_yaxes(autorange="reversed")  # 낮을수록 위로 올라오게
        fig_q.update_layout(paper_bgcolor="#0f172a", plot_bgcolor="#1e293b", font=dict(color="#f8fafc"))
        st.plotly_chart(fig_q, use_container_width=True)

    with ch_col2:
        fig_c = px.line(
            df_trend, x="날짜", y="CANSLIM", color="티커", markers=True,
            title="📊 종목별 CANSLIM 점수 변동 추이",
            labels={"CANSLIM": "CANSLIM 종합 점수"}
        )
        fig_c.update_layout(paper_bgcolor="#0f172a", plot_bgcolor="#1e293b", font=dict(color="#f8fafc"))
        st.plotly_chart(fig_c, use_container_width=True)

    # 스냅샷 테이블
    st.markdown(f"##### 📋 {selected_snap['date']} 스냅샷 종목 전체 목록")
    df_snap = pd.DataFrame(selected_snap["stocks"])
    snap_display_cols = {
        "date": "스냅샷일자",
        "ticker": "티커",
        "name": "기업명",
        "status": "상태",
        "canslim": "CANSLIM 점수",
        "est_quarters": "흑전예상(분기)",
        "rev_growth": "매출성장(YoY)",
        "sbc_ratio": "SBC 비중(%)"
    }
    
    st.dataframe(
        df_snap.rename(columns=snap_display_cols),
        use_container_width=True,
        hide_index=True
    )

    # CSV 다운로드 버튼
    csv_bytes = df_snap.rename(columns=snap_display_cols).to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label=f"📥 {selected_snap['date']} 스냅샷 CSV 다운로드",
        data=csv_bytes,
        file_name=f"turnaround_snapshot_{selected_snap['date']}.csv",
        mime="text/csv"
    )

    st.markdown("---")


# ----------------------------------------------------
# TAB 2: 파트 1 — 26년 2분기 흑전 확정 44선 (CANSLIM)
# ----------------------------------------------------
with tab_part1:
    st.markdown("#### 🏆 26년 2분기 흑자전환 확정 종목 & CANSLIM TOP 순위표")
    st.caption("최근 분기 영업이익 또는 EBITDA가 흑자로 돌아선 44개 기업의 CANSLIM 순위입니다.")

    df_part1 = pd.DataFrame(PART1_STOCKS)

    col_p1, col_p2 = st.columns([1, 2])
    with col_p1:
        st.markdown("##### 🥇 최고점 대표 3개 기업")
        for sitm in [df_part1[df_part1["ticker"] == "SITM"].iloc[0], 
                     df_part1[df_part1["ticker"] == "J"].iloc[0], 
                     df_part1[df_part1["ticker"] == "SMTC"].iloc[0]]:
            st.markdown(f"""
            <div class="metric-card" style="margin-bottom: 0.8rem;">
                <div style="display:flex; justify-content:space-between;">
                    <span style="font-weight:700; color:#38bdf8;">{sitm['name']}</span>
                    <span style="color:#10b981; font-weight:800;">{sitm['canslim']}점</span>
                </div>
                <div style="font-size:0.85rem; color:#94a3b8;">티커: {sitm['ticker']} | 시총: ${sitm['market_cap_b']}B | {sitm['sector']}</div>
            </div>
            """, unsafe_allow_html=True)
            
    with col_p2:
        st.markdown("##### 📋 전체 순위 데이터")
        st.dataframe(
            df_part1.rename(columns={
                "rank": "순위",
                "name": "기업명",
                "ticker": "티커",
                "market_cap_b": "시총 ($B)",
                "canslim": "CANSLIM 점수",
                "sector": "섹터"
            }),
            use_container_width=True,
            hide_index=True,
            height=380
        )

    # CANSLIM 점수 분포 차트
    fig_bar = px.bar(
        df_part1.sort_values("canslim", ascending=False),
        x="ticker",
        y="canslim",
        color="canslim",
        color_continuous_scale="Viridis",
        title="44개 흑자전환 기업 CANSLIM 점수 랭킹",
        labels={"ticker": "종목 티커", "canslim": "CANSLIM 점수"}
    )
    fig_bar.update_layout(paper_bgcolor="#0f172a", plot_bgcolor="#1e293b", font=dict(color="#f8fafc"))
    st.plotly_chart(fig_bar, use_container_width=True)


# ----------------------------------------------------
# TAB 3: 실시간 종목 스캐너 (Live Scanner)
# ----------------------------------------------------
with tab_scanner:
    st.markdown("#### ⚡ 실시간 티커 5단계 필터 검증기")
    st.caption("궁금한 미국 종목의 티커를 입력하면 실시간 재무제표를 바탕으로 5단계 필터 판정 및 흑전 분기를 계산합니다.")

    c_in1, c_in2 = st.columns([3, 1])
    with c_in1:
        input_ticker = st.text_input("티커를 입력하세요 (예: RBLX, SNOW, PLTR, SOFI, PATH, HOOD)", value="RBLX").strip().upper()
    with c_in2:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        scan_btn = st.button("🚀 실시간 스캔 실행", use_container_width=True)

    if scan_btn or input_ticker:
        with st.spinner(f"yfinance에서 {input_ticker}의 분기 재무제표 및 OCF 데이터를 분석 중..."):
            res = analyze_live_ticker(input_ticker)
            
            if res is None:
                st.error(f"❌ {input_ticker}의 재무 데이터를 불러올 수 없습니다. 올바른 미국 상장사 티커인지 확인해 주세요.")
            else:
                pass_color = "#10b981" if res["pass_part2"] else "#ef4444"
                pass_text = "🎉 파트 2 턴어라운드 조건 통과!" if res["pass_part2"] else "⚠️ 파트 2 조건 일부 미달"

                st.markdown(f"""
                <div class="metric-card" style="border-left: 6px solid {pass_color}; margin-top: 1rem;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h3>{res['name']} ({res['ticker']}) - 현재가: ${res['current_price']}</h3>
                        <span style="font-size:1.1rem; font-weight:700; color:{pass_color};">{pass_text}</span>
                    </div>
                    <p style="color:#94a3b8; font-size:0.9rem;">섹터: {res['sector']} | 시총: ${res['market_cap_b']}B</p>
                </div>
                """, unsafe_allow_html=True)

                sc1, sc2, sc3, sc4 = st.columns(4)
                with sc1:
                    st.metric("매출 성장률 (YoY)", f"+{res['rev_growth_yoy']}%", delta="20% 이상 합격" if res['rev_growth_yoy'] >= 20 else "미달", delta_color="normal")
                with sc2:
                    st.metric("GAAP 영업손익", f"${res['op_income_m']}M", delta="적자 상태 (턴어라운드 전조)" if res['op_income_m'] < 0 else "이미 흑자")
                with sc3:
                    st.metric("EBITDA / OCF", f"${res['ebitda_m']}M / ${res['ocf_m']}M", delta="현금흐름 흑자 전환!" if (res['ebitda_positive'] or res['ocf_positive']) else "적자", delta_color="normal")
                with sc4:
                    st.metric("흑전 추정 시점", f"{res['est_quarters_to_gaap']}분기 이내", delta="8분기(2년) 내 합격" if res['est_quarters_to_gaap'] <= 8 else "기간 초과", delta_color="normal")

                st.markdown(f"**CANSLIM 종합 점수:** `{res['canslim']}점` | **SBC(주식보상비용) 매출 대비:** `{res['sbc_ratio']}%`")


# ----------------------------------------------------
# TAB 4: 매일 자동 업데이트 구축 가이드
# ----------------------------------------------------
with tab_automation:
    st.markdown("#### ⚙️ 매일 아침 무료 자동 업데이트(GitHub Actions) 구축 가이드")
    st.caption("비용 0원으로 매일 아침 한국시간 07:30(미국 장 마감 후) 자동으로 최신 종목을 걸러내어 사이트를 갱신하는 방법입니다.")

    st.markdown("""
    ##### 1️⃣ 자동 업데이트 아키텍처 원리
    * 미국 기업들은 장 마감 후 SEC에 10-Q(분기) 실적을 제출합니다.
    * **GitHub Actions**의 무료 크론탭(Cron) 기능을 이용하여 매일 아침 자동으로 스크리닝 파이썬 스크립트를 실행합니다.
    * 새로 걸러진 22개 종목 데이터가 갱신되어 웹 대시보드에 즉시 반영됩니다.

    ##### 2️⃣ 저장소에 포함된 자동화 파일
    워크스페이스에 이미 자동화 스크립트와 워크플로우 설정 파일이 생성되어 있습니다:
    * `update_scheduler.py`: 일 단위 스크리닝 배치 스크립트
    * `.github/workflows/daily_screening.yml`: GitHub Actions 자동화 실행 정의서
    """)

    st.code("""
# .github/workflows/daily_screening.yml 설정 내용
name: Daily Turnaround Stock Screener

on:
  schedule:
    - cron: '30 22 * * 1-5'  # 월~금 UTC 22:30 (한국시간 화~토 07:30)
  workflow_dispatch:        # 수동 실행 지원

jobs:
  screen:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run Screener
        run: python update_scheduler.py
    """, language="yaml")

    st.success("💡 GitHub 리포지토리에 푸시하기만 하면 별도의 서버 비용 없이 매일 평일 아침 자동으로 업데이트됩니다!")
