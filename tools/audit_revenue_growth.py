"""Compare old/new engines against identical captured inputs for preset tickers.

Live:   python tools/audit_revenue_growth.py --output audit-output
Replay: python tools/audit_revenue_growth.py --snapshots audit-output/snapshots.json --output replay
The baseline commit is fixed so a later run never compares against an already-fixed main.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from io import StringIO
import json
from pathlib import Path
import subprocess
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd
import yfinance as yf

import screener_engine as engine
from preset_stocks import PART2_STOCKS

BASELINE = "afca0ebc3b627011bc416fde29925d525b89de67"
INFO_FIELDS = ["shortName", "sector", "marketCap", "currentPrice", "regularMarketPrice",
               "fiftyTwoWeekHigh", "heldPercentInstitutions", "ebitda", "longBusinessSummary"]


def capture(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        fin = stock.quarterly_financials
        cf = stock.quarterly_cashflow
        # Keep only fields actually consumed by both engines.
        fin = fin.loc[fin.index.isin(["Total Revenue", "Operating Income", "EBITDA"])]
        cf = cf.loc[cf.index.isin(["Operating Cash Flow", "Stock Based Compensation"])]
        return {"ticker": ticker, "captured_at_utc": datetime.now(timezone.utc).isoformat(),
                "info": {key: info[key] for key in INFO_FIELDS if key in info},
                "financials": json.loads(fin.to_json(orient="split", date_format="iso")),
                "cashflow": json.loads(cf.to_json(orient="split", date_format="iso"))}
    except Exception as exc:
        return {"ticker": ticker, "error": f"{type(exc).__name__}: {exc}"}


def restore_frame(data):
    frame = pd.read_json(StringIO(json.dumps(data)), orient="split")
    frame.columns = pd.to_datetime(frame.columns)
    return frame


def compare(snapshot, baseline):
    row = {"ticker": snapshot["ticker"], "status": "ok"}
    if "error" in snapshot:
        return {**row, "status": "error", "reason": snapshot["error"]}
    stock = SimpleNamespace(info=snapshot["info"],
                            quarterly_financials=restore_frame(snapshot["financials"]),
                            quarterly_cashflow=restore_frame(snapshot["cashflow"]))
    with patch.object(yf, "Ticker", return_value=stock):
        old = baseline.analyze_live_ticker(row["ticker"])
        new = engine.analyze_live_ticker(row["ticker"])
    if old is None or new is None:
        return {**row, "status": "unavailable", "reason": "필수 재무제표 또는 종목 정보 부족"}
    row.update({"old_qoq_mislabeled_yoy": old["rev_growth_yoy"],
                "new_yoy": new["rev_growth_yoy"],
                "old_growth_pass": bool(old["rev_growth_yoy"] >= 20),
                "new_growth_pass": new["revenue_growth_pass"],
                "old_canslim": old["canslim"], "new_canslim": new["canslim"],
                "old_part2_pass": bool(old["pass_part2"]), "new_part2_pass": new["pass_part2"],
                "revenue_period": new["revenue_period"],
                "revenue_prior_year_period": new["revenue_prior_year_period"],
                "reason": new["rev_growth_reason"]})
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshots", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    code = subprocess.check_output(["git", "show", f"{BASELINE}:screener_engine.py"], cwd=ROOT, text=True)
    baseline = ModuleType("baseline_engine")
    exec(compile(code, f"{BASELINE}:screener_engine.py", "exec"), baseline.__dict__)
    if args.snapshots:
        bundle = json.loads(args.snapshots.read_text())
    else:
        with ThreadPoolExecutor(max_workers=4) as pool:
            snapshots = list(pool.map(capture, [s["ticker"] for s in PART2_STOCKS]))
        bundle = {"source": "Yahoo Finance via yfinance", "yfinance_version": yf.__version__,
                  "baseline_commit": BASELINE, "snapshots": snapshots}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "snapshots.json").write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    rows = []
    for snapshot in bundle["snapshots"]:
        try:
            rows.append(compare(snapshot, baseline))
        except Exception as exc:
            rows.append({"ticker": snapshot["ticker"], "status": "error", "reason": f"{type(exc).__name__}: {exc}"})
    df = pd.DataFrame(rows)
    df.to_csv(args.output / "comparison.csv", index=False)
    ok = df[df["status"] == "ok"]
    summary = {"requested": len(df), "compared": len(ok),
               "errors_or_unavailable": len(df) - len(ok),
               "growth_condition_changed": int((ok["old_growth_pass"] != ok["new_growth_pass"]).sum()) if len(ok) else 0,
               "part2_changed": int((ok["old_part2_pass"] != ok["new_part2_pass"]).sum()) if len(ok) else 0,
               "canslim_changed": int((ok["old_canslim"] != ok["new_canslim"]).sum()) if len(ok) else 0}
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    print(df.drop(columns=["reason"], errors="ignore").to_string(index=False))


if __name__ == "__main__":
    main()
