# claude-quant-lab

An independent systematic-strategy research lab (Claude's competing effort).
Goal: find and validate a strategy that genuinely beats buy-and-hold QQQ on a risk-adjusted (and ideally raw) basis, using edges the neighboring Codex project did not test.

## 2026-07-01 Codex Audit Update

Latest taxable-account strategy spec: [`outputs/FINAL_TAXABLE_BUY_HOLD_SPEC_V2.md`](outputs/FINAL_TAXABLE_BUY_HOLD_SPEC_V2.md).

Latest post-Claude operational spec: [`outputs/FINAL_TAXABLE_BUY_HOLD_SPEC_V3.md`](outputs/FINAL_TAXABLE_BUY_HOLD_SPEC_V3.md).

24/7 market briefing service: [`docs/BRIEFING_SERVICE.md`](docs/BRIEFING_SERVICE.md).

Cloud worker blueprint: [`render.yaml`](render.yaml).

Prior band-rebalanced strategy spec: [`outputs/FINAL_NO_CASH_GLD_STRATEGY.md`](outputs/FINAL_NO_CASH_GLD_STRATEGY.md).

This addendum documents the no-cash, weekly-signal, band-rebalanced, GLD-defensive AI/semis strategy with exact weights, current order sheet, buy/sell rules, tested data modes, benchmarks, exit-rule comparisons, cash-reserve comparisons, and after-tax band-rebalance tests.

Comparison charts: [`outputs/STRATEGY_COMPARISON_CHARTS.md`](outputs/STRATEGY_COMPARISON_CHARTS.md).

Buy-and-hold entry timing tests: [`outputs/BUY_HOLD_ENTRY_TIMING.md`](outputs/BUY_HOLD_ENTRY_TIMING.md).

Catastrophe gate sweep: [`outputs/CATASTROPHE_GATE_BUY_HOLD.md`](outputs/CATASTROPHE_GATE_BUY_HOLD.md).

Backtest code and cached inputs used by the Codex audit are in [`work/`](work/).

Status: bootstrapping — research first, then a lean vectorized backtester.
