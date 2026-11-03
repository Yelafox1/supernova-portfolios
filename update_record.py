#!/usr/bin/env python3
"""Daily update for my SuperNova paper portfolios.

Reads each book's own files (never writes to them), adds any new trades and
the latest NAV, refreshes the table in README.md, hashes everything into
proofs/, timestamps that file with OpenTimestamps, and commits.
Safe to run more than once a day.
"""
import csv, json, os, glob, hashlib, subprocess, datetime as dt
from zoneinfo import ZoneInfo

REC = os.path.dirname(os.path.abspath(__file__))
PERF = "/workspace/supernova_perf/nav_daily.csv"
BOOKS = {  # folder: (source dir, name in perf file)
    "flagship": ("/workspace/supernova_portfolio", "SuperNova Portfolio"),
    "moonshot": ("/workspace/supernova_moonshot", "SuperNova Moonshot"),
}
LABEL = {"flagship": "SuperNova Orbit", "moonshot": "Moonshot"}  # display names only; folder keys stay (flagship = Orbit, renamed Nov 3 2026)
START = "2026-10-31"
OTS = os.path.expanduser("~/.local/bin/ots")
now = dt.datetime.now(ZoneInfo("America/Chicago")); today = now.date().isoformat()
TF = ["timestamp_ct", "ticker", "side", "shares", "price", "reason", "source_id"]
NF = ["date", "nav", "spy_close", "cumulative_return", "source_asof"]

def rows(p):
    return list(csv.DictReader(open(p))) if os.path.exists(p) else []

def write(p, fields, r):
    with open(p, "w", newline="") as fh:
        w = csv.DictWriter(fh, fields); w.writeheader(); w.writerows(r)

perf = rows(PERF)
table = []
for folder, (src, pname) in BOOKS.items():
    out = os.path.join(REC, folder); os.makedirs(out, exist_ok=True)
    st = json.load(open(os.path.join(src, "state.json")))
    led = rows(os.path.join(src, "ledger.csv"))[-1]
    spy = {r["date"]: r["spy_close"] for r in perf if r["portfolio"] == pname}

    trades = rows(f"{out}/trades.csv")
    if not trades:  # starting snapshot of what the book holds today, no history
        import yfinance as yf
        pos = st["positions"]; ts = now.strftime("%Y-%m-%d %H:%M:%S %Z")
        end = (dt.date.fromisoformat(led["date"]) + dt.timedelta(days=1)).isoformat()
        px = yf.download(list(pos), start=led["date"], end=end, progress=False, auto_adjust=False)["Close"].iloc[-1]
        for k, sh in pos.items():
            trades.append(dict(timestamp_ct=ts, ticker=k, side="OPEN_SNAPSHOT", shares=f"{sh:.4f}",
                               price=f"{float(px[k]):.4f}", reason=f"starting position, priced at {led['date']} close",
                               source_id="snapshot"))
        trades.append(dict(timestamp_ct=ts, ticker="CASH", side="OPEN_SNAPSHOT", shares=f"{st.get('cash', 0):.2f}",
                           price="1", reason="starting cash", source_id="snapshot"))
    seen = {t["source_id"] for t in trades}
    for t in rows(os.path.join(src, "trades_log.csv")):
        sid = hashlib.sha256("|".join(t[k] for k in ["date", "ticker", "side", "shares", "price"]).encode()).hexdigest()[:12]
        if t["date"] >= START and sid not in seen:
            trades.append(dict(timestamp_ct=f"{t['date']} (CT session)", ticker=t["ticker"], side=t["side"],
                               shares=t["shares"], price=t["price"], reason=t.get("reason", ""), source_id=sid))
            seen.add(sid)
    write(f"{out}/trades.csv", TF, trades)

    nav = rows(f"{out}/nav.csv")
    if not (nav and nav[-1]["source_asof"] == led["date"]) and not any(n["date"] == today for n in nav):
        base = float(nav[0]["nav"]) if nav else float(led["nav"]); v = float(led["nav"])
        nav.append(dict(date=today, nav=f"{v:.2f}", spy_close=spy.get(led["date"], ""),
                        cumulative_return=f"{v / base - 1:.6f}", source_asof=led["date"]))
    write(f"{out}/nav.csv", NF, nav)
    a, b = nav[0], nav[-1]
    try: vs = f"{float(b['spy_close']) / float(a['spy_close']) - 1:+.2%}"
    except ValueError: vs = "n/a"
    table.append(f"| {LABEL.get(folder, folder.capitalize())} | ${float(a['nav']):,.2f} | ${float(b['nav']):,.2f} ({b['source_asof']}) "
                 f"| {float(b['cumulative_return']):+.2%} | {vs} |")

README = """# SuperNova portfolios

These two portfolios are run entirely by SuperNova, an AI I set up to manage money on its own. It picks the stocks, decides when to buy and sell, and makes every trade, and I don't override it. For now it's paper money, so treat the numbers as hypothetical and not investment advice.

SuperNova works from public market data, company filings, analyst estimates, and congressional and fund holdings disclosures. It also studies the trades of other AI-run portfolios and well-known investors to test and sharpen its own thinking.

The record starts October 31, 2026, with whatever each portfolio held that day. Nothing before that date is included.

{table}

**SuperNova Orbit** is the core portfolio: quality large-cap US stocks with strong growth and momentum, reviewed every week. It caps how much any one stock or theme can hold, keeps a cash buffer, and shifts toward defensive names when markets weaken.

**Moonshot** is the high-risk portfolio, hunting for the next big runner among small and mid-size companies whose sales and analyst estimates are climbing fast. It lets winners run and cuts losers quickly. It started this record already down about 8% from its $6,992 start on Oct 29, and I'm leaving that in.

_Renamed from SuperNova Flagship on Nov 3 2026; prior records under Flagship are the same book._ (Its files still live in the `flagship/` folder.)

Every trade is listed in each portfolio's folder with the reason behind it, and each day's record is timestamped so it can't be changed later.
"""
# README is regenerated from the template above with the live table (edit the template if the strategy changes)
tbl = "| Portfolio | Start (Oct 31) | Latest | Return | SPY same period |\n|---|---|---|---|---|\n" + "\n".join(table)
open(f"{REC}/README.md", "w").write(README.replace("{table}", tbl))

def run(*a, check=True):
    return subprocess.run(a, cwd=REC, check=check, capture_output=True, text=True)

for p in sorted(glob.glob(f"{REC}/proofs/*.ots")):  # finish older proofs once Bitcoin confirms them
    r = run(OTS, "upgrade", p, check=False)
    print("upgrade", os.path.basename(p), (r.stdout + r.stderr).strip().splitlines()[-1:])
    for bak in glob.glob(p + ".bak"): os.remove(bak)

os.makedirs(f"{REC}/proofs", exist_ok=True)
files = ["README.md", "update_record.py"] + [f"{b}/{f}" for b in BOOKS for f in ("trades.csv", "nav.csv")]
man_txt = "".join(f"{hashlib.sha256(open(f'{REC}/{f}', 'rb').read()).hexdigest()}  {f}\n" for f in files)
last = sorted(glob.glob(f"{REC}/proofs/*.sha256"))
if not last or open(last[-1]).read() != man_txt:
    name = f"{REC}/proofs/{today}.sha256"
    if os.path.exists(name): name = f"{REC}/proofs/{today}_{now:%H%M}.sha256"
    open(name, "w").write(man_txt)
    r = run(OTS, "stamp", name, check=False); print("stamp", os.path.basename(name), r.returncode)

run("git", "add", "-A")
if run("git", "diff", "--cached", "--quiet", check=False).returncode:
    run("git", "commit", "-m", f"Update for {today}"); print("committed")
else:
    print("nothing new")
