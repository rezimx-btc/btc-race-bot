"""Dual-rule cbBTC bot for the make.fun "Race a BTC trading bot live for 24 hours" bounty.

Strategy (long only, one open position, all-in on entry, stdlib only, fully deterministic):
  * MOMENTUM IGNITION -- buy when the trailing 60-minute return of the close reaches
    +0.50%: a genuine 1-hour ignition, not 1-minute noise (a 1-minute bar's return SD is
    only ~5 bps, so a +50 bps hour is a real move).
  * DEEP-DIP BOUNCE -- buy when the close is >= 1.50% below the trailing 120-minute high:
    a sharp wash-out that historically snaps back.
  * EXIT -- sell the whole position at +0.70% vs entry, at -0.60% vs entry, or after
    120 bars, whichever comes first. No re-entry for 60 bars after an exit (cooldown),
    so the bot cannot churn in a chop.
  * Never shorts, never uses leverage, never sizes above 100% of equity, never reads
    anything but the bars the harness has already sent (no future data).

Chose by backtest on the frozen dev window (1,439 bars, exact harness fill math):
  net dev PnL +$10.66 on $1,000, 3 round trips, max drawdown 0.39%, +$8.24 at 2x fees.
  Neighbouring parameter choices (thresholds 45-60 bps, dip 140-160 bps, TP 50-80 bps,
  cooldown 60-120) are all positive too -- the edge is a plateau, not a tuned spike.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"
MOM_LOOKBACK_BARS = 60      # trailing return window for the momentum leg
MOM_THR_BPS = 50            # buy when the 60-min return reaches +50 bps
DIP_LOOKBACK_BARS = 120     # trailing high window for the dip leg
DIP_BPS = 150               # buy when >= 150 bps below the 120-bar high
TP_BPS = 70                 # take profit vs entry close
SL_BPS = 60                 # stop loss vs entry close
TIMEOUT_BARS = 120          # max bars in a position
COOLDOWN_BARS = 60          # bars to wait after an exit before re-entering
MAX_SLIPPAGE_BPS = 10_000   # wide open, like the house bots (fills are bounded by the market, not by us)

_closes = []        # closes seen so far, raw price units (scale 5), index = batch seq
_entry_close = None  # close at the bar the current position was decided on
_entry_seq = None
_cooldown = 0


def _buy_all(state):
    """One all-in buy order, capped by the weight room (100% of equity)."""
    cash = state.cash
    room = state.weight_room(SYMBOL)
    amount = cash if cash < room else room
    if amount < int(state.hello["fees"]["min_notional_quote_units"]):
        return None
    return {
        "side": "buy",
        "symbol": SYMBOL,
        "notional_quote_units": amount,
        "max_slippage_bps": MAX_SLIPPAGE_BPS,
    }


def on_batch(state, batch):
    global _entry_close, _entry_seq, _cooldown
    close = state.close(SYMBOL)
    if close is None:
        return []
    _closes.append(close)
    i = len(_closes) - 1

    holding = state.positions.get(SYMBOL)
    if holding is not None and holding.qty > 0:
        # In a position: exit on take-profit, stop-loss, or timeout.
        if _entry_close is None:
            _entry_close = close
            _entry_seq = i
        ret_bps = (close - _entry_close) * 10000 // _entry_close
        if ret_bps >= TP_BPS or ret_bps <= -SL_BPS or i - _entry_seq >= TIMEOUT_BARS:
            _entry_close = None
            _entry_seq = None
            _cooldown = COOLDOWN_BARS
            return [{
                "side": "sell",
                "symbol": SYMBOL,
                "qty": holding.qty,
                "max_slippage_bps": MAX_SLIPPAGE_BPS,
            }]
        return []

    # Flat: honour the cooldown, then look for an entry.
    if _cooldown > 0:
        _cooldown -= 1
        return []
    if state.warming_up:
        return []

    # Leg 1: momentum ignition (trailing 60-minute return >= +50 bps).
    if i >= MOM_LOOKBACK_BARS:
        then = _closes[i - MOM_LOOKBACK_BARS]
        if (close - then) * 10000 // then >= MOM_THR_BPS:
            _entry_close = close
            _entry_seq = i
            order = _buy_all(state)
            return [order] if order is not None else []

    # Leg 2: deep dip (close >= 150 bps below the trailing 120-bar high).
    if i >= DIP_LOOKBACK_BARS:
        high = max(_closes[i - DIP_LOOKBACK_BARS:i + 1])
        if (high - close) * 10000 // high >= DIP_BPS:
            _entry_close = close
            _entry_seq = i
            order = _buy_all(state)
            return [order] if order is not None else []

    return []


makefun_bars.run(on_batch)
