"""
체슬리 턴어라운드 스크리너 날짜별 누적 히스토리 데이터셋
- 2026-09-27 (초기 베이스라인 스냅샷)
- 2026-10-08 (중간 점검)
- 2026-10-15 (방송 시점 스냅샷)
- 2026-10-22 (전주 업데이트)
- 2026-10-29 (금일 최신 업데이트)
"""

HISTORY_TIMELINE = [
    {
        "date": "2026-10-29",
        "label": "2026-10-29 (최신 업데이트)",
        "total_count": 22,
        "new_entries": ["TTAN", "QXO"],
        "dropped_out": ["SMTC"],
        "accelerated": ["NTRA", "RBLX", "ASTS"],
        "summary": "ServiceTitan(TTAN) 및 QXO가 신규 5단계 필터(8분기 내 흑전)를 통과하여 신규 편입. Natera(NTRA)와 Roblox(RBLX)는 현금흐름 개선 가속화로 흑전 예상 시점 4분기 이내로 단축.",
        "stocks": [
            {"date": "2026-10-29", "ticker": "NTRA", "name": "Natera, Inc.", "status": "유지 (가속)", "canslim": 74.0, "est_quarters": 4, "rev_growth": 37.7, "sbc_ratio": 13.7},
            {"date": "2026-10-29", "ticker": "RBLX", "name": "Roblox Corp", "status": "유지 (가속)", "canslim": 76.0, "est_quarters": 4, "rev_growth": 29.4, "sbc_ratio": 21.0},
            {"date": "2026-10-29", "ticker": "ASTS", "name": "Space Exploration (ASTS)", "status": "유지 (가속)", "canslim": 85.0, "est_quarters": 5, "rev_growth": 91.9, "sbc_ratio": 10.6},
            {"date": "2026-10-29", "ticker": "TTAN", "name": "ServiceTitan, Inc.", "status": "신규 편입 🟢", "canslim": 72.0, "est_quarters": 6, "rev_growth": 25.0, "sbc_ratio": 15.0},
            {"date": "2026-10-29", "ticker": "QXO", "name": "QXO, Inc.", "status": "신규 편입 🟢", "canslim": 75.0, "est_quarters": 4, "rev_growth": 45.0, "sbc_ratio": 6.5},
            {"date": "2026-10-29", "ticker": "SNOW", "name": "Snowflake Inc.", "status": "유지", "canslim": 73.0, "est_quarters": 6, "rev_growth": 28.9, "sbc_ratio": 29.5},
            {"date": "2026-10-29", "ticker": "U", "name": "Unity Software Inc", "status": "유지", "canslim": 69.5, "est_quarters": 7, "rev_growth": 22.1, "sbc_ratio": 16.8},
            {"date": "2026-10-29", "ticker": "XMTR", "name": "Xometry, Inc.", "status": "유지", "canslim": 71.0, "est_quarters": 5, "rev_growth": 24.8, "sbc_ratio": 8.9},
            {"date": "2026-10-29", "ticker": "RBRK", "name": "Rubrik, Inc.", "status": "유지", "canslim": 72.5, "est_quarters": 5, "rev_growth": 35.2, "sbc_ratio": 18.5},
            {"date": "2026-10-29", "ticker": "AEHR", "name": "AEHR Test Systems", "status": "유지", "canslim": 68.0, "est_quarters": 6, "rev_growth": 28.5, "sbc_ratio": 7.2},
            {"date": "2026-10-29", "ticker": "PL", "name": "Planet Labs PBC", "status": "유지", "canslim": 67.5, "est_quarters": 6, "rev_growth": 22.8, "sbc_ratio": 15.3},
            {"date": "2026-10-29", "ticker": "GKOS", "name": "GLAUKOS Corp", "status": "유지", "canslim": 70.0, "est_quarters": 6, "rev_growth": 23.5, "sbc_ratio": 11.2},
            {"date": "2026-10-29", "ticker": "MP", "name": "MP Materials Co", "status": "유지", "canslim": 68.0, "est_quarters": 5, "rev_growth": 24.0, "sbc_ratio": 5.5},
            {"date": "2026-10-29", "ticker": "CSTL", "name": "Castle Biosciences", "status": "유지", "canslim": 69.0, "est_quarters": 5, "rev_growth": 33.2, "sbc_ratio": 8.4},
            {"date": "2026-10-29", "ticker": "BRZE", "name": "Braze, Inc.", "status": "유지", "canslim": 67.0, "est_quarters": 6, "rev_growth": 26.3, "sbc_ratio": 17.2},
            {"date": "2026-10-29", "ticker": "IRTC", "name": "iRhythm Technologies", "status": "유지", "canslim": 66.0, "est_quarters": 7, "rev_growth": 21.0, "sbc_ratio": 12.0},
            {"date": "2026-10-29", "ticker": "BKSY", "name": "BlackSky Technology", "status": "유지", "canslim": 65.0, "est_quarters": 7, "rev_growth": 31.5, "sbc_ratio": 10.8},
            {"date": "2026-10-29", "ticker": "STLN", "name": "Starling Oncology", "status": "유지", "canslim": 64.0, "est_quarters": 7, "rev_growth": 34.0, "sbc_ratio": 9.5},
            {"date": "2026-10-29", "ticker": "EVLV", "name": "Evolv Technology", "status": "유지", "canslim": 63.0, "est_quarters": 6, "rev_growth": 27.5, "sbc_ratio": 9.8},
            {"date": "2026-10-29", "ticker": "TE", "name": "T1 Energy Inc.", "status": "유지", "canslim": 62.0, "est_quarters": 6, "rev_growth": 29.0, "sbc_ratio": 6.8},
            {"date": "2026-10-29", "ticker": "LASR", "name": "nLIGHT, INC.", "status": "유지", "canslim": 61.5, "est_quarters": 7, "rev_growth": 20.5, "sbc_ratio": 8.0},
            {"date": "2026-10-29", "ticker": "FSLY", "name": "Fastly, Inc.", "status": "유지", "canslim": 61.0, "est_quarters": 8, "rev_growth": 21.4, "sbc_ratio": 14.1}
        ]
    },
    {
        "date": "2026-10-22",
        "label": "2026-10-22 (전주 스냅샷)",
        "total_count": 21,
        "new_entries": ["ASTS"],
        "dropped_out": [],
        "accelerated": ["NTRA"],
        "summary": "우주 통신 저궤도 위성 테마인 ASTS가 매출성장률 91.9% 및 EBITDA 흑전 지표를 확인하며 신규 진입.",
        "stocks": [
            {"date": "2026-10-22", "ticker": "NTRA", "name": "Natera, Inc.", "status": "유지", "canslim": 73.0, "est_quarters": 5, "rev_growth": 36.5, "sbc_ratio": 14.0},
            {"date": "2026-10-22", "ticker": "RBLX", "name": "Roblox Corp", "status": "유지", "canslim": 74.5, "est_quarters": 5, "rev_growth": 28.5, "sbc_ratio": 21.5},
            {"date": "2026-10-22", "ticker": "ASTS", "name": "Space Exploration (ASTS)", "status": "신규 편입 🟢", "canslim": 83.0, "est_quarters": 6, "rev_growth": 88.0, "sbc_ratio": 11.0},
            {"date": "2026-10-22", "ticker": "SNOW", "name": "Snowflake Inc.", "status": "유지", "canslim": 72.0, "est_quarters": 6, "rev_growth": 28.0, "sbc_ratio": 30.0},
            {"date": "2026-10-22", "ticker": "U", "name": "Unity Software Inc", "status": "유지", "canslim": 69.0, "est_quarters": 7, "rev_growth": 21.8, "sbc_ratio": 17.0},
            {"date": "2026-10-22", "ticker": "XMTR", "name": "Xometry, Inc.", "status": "유지", "canslim": 70.0, "est_quarters": 5, "rev_growth": 24.0, "sbc_ratio": 9.0},
            {"date": "2026-10-22", "ticker": "SMTC", "name": "Semtech Corp", "status": "유지", "canslim": 41.3, "est_quarters": 8, "rev_growth": 11.3, "sbc_ratio": 6.5}
        ]
    },
    {
        "date": "2026-10-15",
        "label": "2026-10-15 (방송 공개 시점)",
        "total_count": 22,
        "new_entries": ["RBLX", "SNOW", "U", "NTRA", "PL"],
        "dropped_out": [],
        "accelerated": [],
        "summary": "체슬리TV [별주부전] 탑엔드 학습부장 첫 발표 시점의 22개 유망주 공식 포트폴리오 스냅샷.",
        "stocks": [
            {"date": "2026-10-15", "ticker": "NTRA", "name": "Natera, Inc.", "status": "최초 편입", "canslim": 74.0, "est_quarters": 6, "rev_growth": 37.7, "sbc_ratio": 13.7},
            {"date": "2026-10-15", "ticker": "RBLX", "name": "Roblox Corp", "status": "최초 편입", "canslim": 73.0, "est_quarters": 6, "rev_growth": 27.8, "sbc_ratio": 22.0},
            {"date": "2026-10-15", "ticker": "SNOW", "name": "Snowflake Inc.", "status": "최초 편입", "canslim": 71.5, "est_quarters": 7, "rev_growth": 27.5, "sbc_ratio": 31.0},
            {"date": "2026-10-15", "ticker": "U", "name": "Unity Software Inc", "status": "최초 편입", "canslim": 68.0, "est_quarters": 8, "rev_growth": 21.0, "sbc_ratio": 17.5},
            {"date": "2026-10-15", "ticker": "PL", "name": "Planet Labs PBC", "status": "최초 편입", "canslim": 67.5, "est_quarters": 6, "rev_growth": 22.8, "sbc_ratio": 15.3}
        ]
    }
]

def get_snapshot_by_date(date_str):
    for snap in HISTORY_TIMELINE:
        if snap["date"] == date_str:
            return snap
    return HISTORY_TIMELINE[0]

def get_all_snapshots():
    return HISTORY_TIMELINE
