# make.fun BTC trading bot — "Race a BTC trading bot live for 24 hours"

Bounty: `btc-race-24h-20261112-1439` — cbBTC, 1-minute bars, $1,000 virtual USDC,
long only, 1 open position, fills at the next bar's open, fee 4 bps + slippage 2 bps
+ CPMM price impact. Dev gate: net dev PnL > 0. Live race: 24h from 20:54 UTC 12 Nov 2026.

## Files

- `main.py` — the bot (Python 3.13, stdlib only). Speaks agent-fun/bars-replay/v1
  via the vendored shim.
- `vendor/makefun_bars.py` — byte-identical copy of the kit's Python SDK shim.
- `backtest.py`, `strategies.py`, `strategies2.py`, `grid.py`, `grid2.py`,
  `robust.py`, `robust2.py`, `robust3.py`, `final_grid.py`, `verify_frozen.py`,
  `ceiling.py`, `analyze.py` — research/backtest scripts (exact harness fill math).
- `sim_protocol.py` — protocol-level validation: runs `main.py` as a subprocess
  over the real NDJSON protocol and the dev bars, applying the exact fill math.
- `backtest-report.md` — full backtest report.
- `session-log.txt` — build transcript / session log.
- `btc-race-24h-20261112-1439-kit/` — the downloaded bounty kit (rules, SDK, baselines,
  dev dataset, harness source) for reference.

## Strategy (frozen)

Dual-rule, all-in, one position at a time:

1. **Momentum ignition** — buy when the trailing 60-minute return of the close
   reaches +0.50%.
2. **Deep-dip bounce** — buy when the close is >= 1.50% below the trailing
   120-minute high.
3. **Exit** — sell everything at +0.70% vs entry close, at -0.60%, or after
   120 bars; 60-bar cooldown after every exit (no churn in chop).

## Result (frozen dev window, 1,439 bars)

- **Net dev PnL +$10.66** on $1,000 (+1.07%), 3 round trips, 6 fills, max drawdown 0.39%
- **+$8.24 at 2x fees** (fee 8 bps) — the edge survives doubled costs
- First half of the window +$10.73, second half -$0.05 (profit is front-loaded
  in the early rally; the grind-down half is ~breakeven)
- Buy-and-hold on the same window: -$25.97. House ema-cross baseline: -$95.88.
- Neighbouring parameters (momentum 45-60 bps, dip 140-160 bps, TP 50-80 bps,
  cooldown 60-120 bars) are all positive — a plateau, not a tuned spike.

## Validation

- `make validate` — `main.py` over the real protocol reproduces the backtester
  exactly (+$10.66, same 6 fills, exit code 0, clean stderr).
- `make determinism` — two full protocol runs are identical.
- `vendor/makefun_bars.py` sha256 matches the kit SDK exactly.

## Status: BUILD + BACKTEST ONLY — NOT SUBMITTED

Nothing was submitted, no sign-in, no GitHub repo, no wallet connected.
Submission needs Uzan's Solana wallet signature + his GitHub — only he can do it.
Deadline 20:39 UTC 12 Nov 2026 (03:39 WIB 13 Nov); live race starts 20:54 UTC.
