#!/usr/bin/env python3
"""Daily append for the SuperNova Flagship public paper record.
READ-ONLY on the source: /workspace/supernova_portfolio (never writes there).
Idempotent: trades keyed by source trade_id, NAV keyed by date. Then git commit + OpenTimestamps."""
import csv, json, os, sys, glob, hashlib, subprocess, datetime as dt
from zoneinfo import ZoneInfo
SRC = "/workspace/supernova_portfolio"          # SuperNova Flagship (formerly "SuperNova Portfolio")
PERF = "/workspace/supernova_perf/nav_daily.csv"  # Plumber's perf tracker (SPY close)
BOOK = "SuperNova Portfolio"
REC = os.path.dirname(os.path.abspath(__file__))
START = "2026-10-31"
OTS = os.path.expanduser("~/.local/bin/ots")
CT = ZoneInfo("America/Chicago")
now = dt.datetime.now(CT); today = now.date().isoformat()
TF = ["timestamp_ct","ticker","side","shares","price","reason","source_id"]
NF = ["date","nav","spy_close","cumulative_return","source_asof"]

def rows(p):
    return list(csv.DictReader(open(p))) if os.path.exists(p) else []
def write(p, f, r):
    with open(p, "w", newline="") as fh:
        w = csv.DictWriter(fh, f); w.writeheader(); w.writerows(r)

st = json.load(open(os.path.join(SRC, "state.json")))
led = rows(os.path.join(SRC, "ledger.csv"))[-1]
spy = {r["date"]: r["spy_close"] for r in rows(PERF) if r["portfolio"] == BOOK}
trades = rows(f"{REC}/trades.csv")
if not trades:  # opening snapshot (not history), valued at closes of the ledger's last date
    import yfinance as yf
    ts = now.strftime("%Y-%m-%d %H:%M:%S %Z"); pos = st["positions"]
    px = yf.download(list(pos), start=led["date"], end=(dt.date.fromisoformat(led["date"])+dt.timedelta(days=1)).isoformat(),
                     progress=False, auto_adjust=False)["Close"].iloc[-1]
    for k, sh in pos.items():
        trades.append(dict(timestamp_ct=ts, ticker=k, side="OPEN_SNAPSHOT", shares=f"{sh:.4f}", price=f"{float(px[k]):.4f}",
            reason=f"Opening position snapshot (paper), valued at {led['date']} close", source_id="snapshot"))
    trades.append(dict(timestamp_ct=ts, ticker="CASH", side="OPEN_SNAPSHOT", shares=f"{st['cash']:.2f}", price="1",
        reason="Opening cash snapshot (paper)", source_id="snapshot"))
seen = {t["source_id"] for t in trades}
for t in rows(os.path.join(SRC, "trades_log.csv")):
    sid = hashlib.sha256("|".join(t[k] for k in ["date","ticker","side","shares","price"]).encode()).hexdigest()[:12]
    if t["date"] >= START and sid not in seen:  # only trades after the record start
        trades.append(dict(timestamp_ct=f"{t['date']} (CT session)", ticker=t["ticker"], side=t["side"], shares=t["shares"],
            price=t["price"], reason=t.get("reason",""), source_id=sid)); seen.add(sid)
write(f"{REC}/trades.csv", TF, trades)

nav = rows(f"{REC}/nav.csv")
if nav and nav[-1]["source_asof"] == led["date"]:
    print("Source NAV not updated since", led["date"], "- no new NAV row")
elif not any(n["date"] == today for n in nav):
    base = float(nav[0]["nav"]) if nav else float(led["nav"]); v = float(led["nav"])
    nav.append(dict(date=today, nav=f"{v:.2f}", spy_close=spy.get(led["date"], ""), cumulative_return=f"{v/base-1:.6f}", source_asof=led["date"]))
write(f"{REC}/nav.csv", NF, nav)

def run(*a, check=True): return subprocess.run(a, cwd=REC, check=check, capture_output=True, text=True)
# upgrade older proofs (pending -> Bitcoin-confirmed)
for p in sorted(glob.glob(f"{REC}/proofs/*.ots")):
    r = run(OTS, "upgrade", p, check=False); print("upgrade", os.path.basename(p), (r.stdout+r.stderr).strip().splitlines()[-1:] )
    for b in glob.glob(p + ".bak"): os.remove(b)
os.makedirs(f"{REC}/proofs", exist_ok=True)
man = f"{REC}/proofs/{today}.sha256"
if not os.path.exists(man + ".ots"):
    with open(man, "w") as fh:
        for f in ["README.md", "trades.csv", "nav.csv", "update_record.py"]:
            fh.write(f"{hashlib.sha256(open(f'{REC}/{f}','rb').read()).hexdigest()}  {f}\n")
    r = run(OTS, "stamp", man, check=False); print("stamp:", r.returncode, (r.stdout+r.stderr).strip())
run("git", "add", "-A")
if run("git", "diff", "--cached", "--quiet", check=False).returncode:
    run("git", "commit", "-m", f"Record update {today} (CT)"); print("committed")
else: print("nothing to commit")
