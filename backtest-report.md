# Backtest report — make.fun BTC trading bot (`btc-race-24h-20261112-1439`)

Date: 2026-11-12 (built ~18:40–19:45 UTC). Deadline 20:39 UTC 12 Nov 2026.
**Status: BUILD + BACKTEST ONLY — NOT SUBMITTED.** No sign-in, no GitHub repo,
no wallet connected. Submission needs Uzan's Solana wallet signature + his GitHub.

## The competition (authoritative rules = the kit, not the bounty page summary)

- cbBTC (CBBTC), 1-minute on-chain bars, $1,000 virtual USDC start, long only,
  max 1 open position, max 16 orders/reply, buy up to 100% of equity.
- Orders decided on bar k fill at bar k+1's open. Fee 4 bps + slippage 2 bps +
  CPMM price impact vs the open's pool depth (~26 bps per full round trip at $1,000).
- Min notional 1 USDC. Dev gate: net dev PnL > 0. Race window needs >= 1 trade
  and max drawdown <= 25%. Final holdings flattened at the last close.
- The parent brief's "$0.04/order + 0.035%" fee description was wrong; the kit's
  4 bps / 2 bps + impact governs. The "50% per minute" cap in the brief is also
  wrong: `max_weight_bps: 10000` = 100% of equity.
- Dev window: 1,439 bars (one 2-minute gap after bar 976), first close $73,739.38,
  last close $72,044.01. Buy-and-hold on the window: **-$25.97** (-2.30%).

## Chosen strategy — dual-rule, all-in, one position (see `main.py`)

1. **Momentum ignition** — buy when the trailing 60-minute return of the close
   reaches **+0.50%**. (A 1-minute bar's return SD is only ~5 bps, so a +50 bps
   hour is a real move, not noise.)
2. **Deep-dip bounce** — buy when the close is **>= 1.50% below the trailing
   120-minute high**.
3. **Exit** — sell everything at **+0.70%** vs entry close, at **-0.60%**, or after
   **120 bars**; **60-bar cooldown** after every exit (no churn in chop).
4. Never shorts, never leverage, never above 100% equity, reads only bars the
   harness already sent. Fully deterministic (no clock, no randomness, no env).

## Dev-window backtest (exact harness fill math, integer arithmetic)

| Metric | Value |
|---|---|
| Net dev PnL | **+$10.66** (+1.07% on $1,000) |
| Trades | 3 round trips, 6 fills |
| Max drawdown | 0.39% |
| Fees paid | $2.42 |
| Net PnL at 2x fees (8 bps) | +$8.24 |
| First half (bars 0–719) | +$10.73 |
| Second half (bars 720–1438) | -$0.05 |
| Guardrails | >= 1 trade: yes (3); max drawdown 0.39% <= 25%: yes |

Fills (protocol-validated run of `main.py`):
- BUY bar 62 @ $74,064.07 ($1,000.00) — momentum ignition in the early rally
- SELL bar 160 @ $74,595.85 (+$6.37 net)
- BUY bar 514 @ $73,579.17 ($1,006.37) — deep dip
- SELL bar 559 @ $73,957.06 (+$4.36 net)
- BUY bar 1427 @ $71,906.22 ($1,010.73) — deep dip near the end
- SELL bar 1438 @ $71,958.57 (window flatten, -$0.07 net)

## Robustness (why this is not a tuned spike)

- Neighbourhood (full window, 2x-fee in brackets): momentum 45 bps +$5.71 (+$2.51),
  55 bps +$9.40 (+$6.99), 60 bps +$9.40 (+$6.99); dip 140 bps +$9.67 (+$7.26),
  160 bps +$11.42 (+$9.00); TP 50 bps +$5.82 (+$3.42), 70 bps +$10.66 (+$8.24),
  80 bps +$11.18 (+$8.76); SL 50/80/100 bps identical (+$9.57, SL never binds);
  timeout 180 identical; cooldown 120 identical (+$9.57), 30 bps +$5.21.
  Bad neighbours: timeout 90 (+$2.05, 2x-fee -$0.35), cooldown 0 (-$1.75),
  momentum 40 bps any-bar (-$0.55) — the chosen point sits mid-plateau.
- Split-half: profit is front-loaded (early rally). The grind-down half is
  ~breakeven (-$0.05), not a loss — the bot sits in cash for long stretches
  (bars 160–514 and 559–1427) rather than churning.
- DP hindsight ceiling on this window is ~+$45 (14 perfect round trips), so
  +$10.66 is far from the ceiling — the bot is selective, not overfit to the
  window's noise.

## What did NOT work (tested and rejected)

- Buy-and-hold -$25.97; momentum (buy bar 24, hold) -$23.31.
- House ema-cross baseline: -$95.88, 68 trades, maxDD 10.00% (whipsaw city).
- Dip-bounce alone (various thresholds): -$11 to -$43 — in a grind-down, dips keep dipping.
- EMA trend / slow-EMA / Donchian / Keltner / RSI mean-reversion: all negative
  (-$9 to -$150); RSI/Keltner churn catastrophically (44–120 trades).
- Hourly-boundary momentum alone: +$3.81. Dip-140 alone: +$3.30. Combined dual:
  +$8.88; with any-bar momentum at 50 bps + cooldown: **+$10.66**.

## Validation

- `make validate` (`sim_protocol.py`): `main.py` run as a subprocess over the real
  NDJSON protocol (hello -> 1,439 batches -> done) with the exact integer fill math
  reproduces the backtester **exactly**: +$10.66, same 6 fills, exit code 0,
  empty stderr.
- `make determinism`: two full protocol runs are identical (byte-for-byte outputs).
- `vendor/makefun_bars.py` sha256 = kit SDK sha256
  (`80452b00d2eb1e9c959e73d41cda6ca726cdbe7bfa4065d48278c22eccd276ff`).
- One data quirk: a single 2-minute gap after bar 976; none of the bot's fills is
  near it, so it cannot change the dev result.

## Risks / honest notes

- Dev rank does not carry to the live race; the live 24h window (from 20:54 UTC)
  is unseen. The bot's edge is selective (3 trades/day), so a flat live window
  likely ends near $0 (gate needs > $0 on dev only; live ranking is by live PnL).
- The bot's profit came mostly from the early rally + one dip bounce. If the live
  window has no rally and no sharp dip, it may trade little and finish ~flat.
- The leaderboard's top dev entries (~+$28) are far above this bot; they may be
  more finely tuned to the dev window (which would not transfer live) or genuinely
  better timed. This bot was deliberately kept general.

## How to run

- `make backtest` — backtest the frozen strategy on the dev window.
- `make validate` — protocol-level validation of `main.py`.
- `make determinism` — two runs must match.
