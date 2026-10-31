# SuperNova Flagship — public paper track record

> **PAPER / HYPOTHETICAL.** No real money is invested. Results are simulated fills on a paper ledger and are not indicative of future results. Not investment advice.

- **Portfolio:** SuperNova Flagship (formerly "SuperNova Portfolio"; ~$6,992 paper start on 2026-10-29; source `supernova_portfolio`)
- **Universe:** long-only US stocks and ETFs, with a cash sleeve
- **Record start:** October 31, 2026. `trades.csv` begins with an **opening snapshot** of the holdings on that date. Earlier history is deliberately not backfilled.
- **Benchmark:** SPY close

## Files
- `trades.csv`: timestamp (CT), ticker, side, shares, price, reason, source_id. Rows are appended only.
- `nav.csv`: date, NAV (USD, paper), SPY close, cumulative return since the record start, and source valuation date.
- `proofs/YYYY-MM-DD.sha256` (+ `.ots`): SHA-256 hashes of each day's files, timestamped with [OpenTimestamps](https://opentimestamps.org/) on the Bitcoin blockchain.
- `update_record.py`: the daily append script. It is idempotent.

## How verification works
1. Every day, the hashes of `trades.csv`/`nav.csv` are written to `proofs/<date>.sha256` and timestamped with `ots stamp`. Within a few hours the proof is anchored in a Bitcoin block, and later runs `ots upgrade` it to a full proof.
2. To verify, check out the commit from that day and run `sha256sum -c proofs/<date>.sha256`, then `ots verify proofs/<date>.sha256.ots`. This shows the file contents existed no later than the Bitcoin block time, so entries cannot be backdated.
3. Git history (and GitHub push timestamps, once published) shows that rows are only ever appended, never rewritten.
