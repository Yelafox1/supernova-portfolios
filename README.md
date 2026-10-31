# SuperNova portfolios

I'm Kaleb Fox, and this is where I keep a public record of two portfolios I run with paper money. No real money is in these. The trades are simulated, so treat the numbers as hypothetical and don't take any of it as investment advice.

I started this record on October 31, 2026. Each portfolio begins with a snapshot of what it held that day. I didn't backfill anything from before that date.

- **Flagship** is my main book: long-only US stocks and ETFs, plus a T-bill ETF (BIL) as cash.
- **Moonshot** is the high-risk book: around 10 small and mid caps. It started the record already down about 8% from its $6,992 start on Oct 29, and I'm leaving that in.

<!-- table -->
| Book | Start (Oct 31) | Latest | Return | SPY same period |
|---|---|---|---|---|
| Flagship | $6,843.88 | $6,843.88 (2026-10-30) | +0.00% | +0.00% |
| Moonshot | $6,438.31 | $6,438.31 (2026-10-30) | +0.00% | +0.00% |
<!-- /table -->

Returns are measured from October 31. The SPY column shows how SPY did over the same stretch.

## What's in here

Each folder has `trades.csv` (every buy and sell, with my reason) and `nav.csv` (daily value next to the SPY close). `update_record.py` adds the day's trades and values.

## Checking the dates

Every update writes hashes of the files to `proofs/`, and that file gets timestamped on the Bitcoin blockchain with [OpenTimestamps](https://opentimestamps.org/). To check a day, check out that commit, run `sha256sum -c proofs/<file>.sha256`, then `ots verify proofs/<file>.sha256.ots`. That shows the files existed by that date, so I can't go back and change them later.
