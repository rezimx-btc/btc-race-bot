# make.fun "Race a BTC trading bot live for 24 hours" -- btc-race-24h-20261112-1439
# Build + backtest only. NO submission here (submission needs Uzan's Solana
# wallet signature + his GitHub, which only he can do).

PYTHON ?= python3

.PHONY: backtest validate determinism clean help

help:
	@echo "make backtest    - exact-fill backtest of the frozen strategy on the dev window"
	@echo "make validate    - run main.py over the real NDJSON protocol (subprocess) and compare"
	@echo "make determinism - two full protocol runs must be identical"
	@echo "make clean       - remove python caches"

backtest:
	$(PYTHON) verify_frozen.py

validate:
	$(PYTHON) sim_protocol.py

determinism:
	$(PYTHON) sim_protocol.py > /tmp/makefun-run-a.txt
	$(PYTHON) sim_protocol.py > /tmp/makefun-run-b.txt
	diff /tmp/makefun-run-a.txt /tmp/makefun-run-b.txt && echo "determinism OK: two runs identical"

clean:
	rm -rf vendor/__pycache__ __pycache__
