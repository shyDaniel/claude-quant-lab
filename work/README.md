# Codex Audit Backtest Code

This folder contains the Codex audit/backtest scripts used to generate the risk-seeking strategy reports in `outputs/`.

The scripts were copied from the independent audit harness so the repository contains the research code, not only the final markdown conclusions.

## Runtime

Python dependencies used by these scripts:

```text
numpy
pandas
matplotlib
tabulate
yfinance
```

The scripts are plain Python and write artifacts to `outputs/`.

## Cached Data

`work/cache/` contains the cached CSV inputs used by the final runs:

- `grid_prices.csv` - adjusted close prices for the AI/semis grid.
- `grid_open_prices.csv` - adjusted open prices for timing-mode tests.
- `grid_fundamentals_raw.csv` - yfinance fundamental snapshot used for market-cap and earnings transforms.
- `gld_prices.csv` - adjusted GLD open/close data used by the GLD defensive-sleeve runs.
- `return_seeker_prices.csv` - earlier return-seeker price cache.
- `audit_adjclose.csv` - earlier audit adjusted-close cache.

The cache is included for reproducibility. The data is public-market/yfinance-derived and should be refreshed before relying on a new live trade date.

## Script Map

| Script | Purpose | Main outputs |
|---|---|---|
| `audit_backtests.py` | Independent baseline audit of QQQ/core/AI strategies. | `outputs/AUDIT_VERDICT.md`, audit metrics |
| `return_seeker_backtest.py` | Initial return-seeking AI tilt from the user's portfolio. | `outputs/TODAY_BUY_PLAN.md`, `outputs/RETURN_SEEKER_PLAN.md` |
| `grid_marketcap_earnings_backtest.py` | Early market-cap/earnings weighted AI grid. | weighted strategy reports |
| `fast_grid_weight_timing.py` | Fast grid adding AVGO/INTC and timing modes. | `outputs/FAST_GRID_WEIGHT_TIMING.md` |
| `transform_grid_search.py` | Cap/earnings transform grid. | `outputs/TRANSFORM_GRID_UPDATE.md` |
| `medium_transform_grid.py` | Expanded transform grid and selected base model. | `outputs/MEDIUM_TRANSFORM_GRID_SEARCH.md` |
| `nbis_storage_tilt_grid.py` | NBIS conviction floor and storage-cap grid. | `outputs/NBIS_STORAGE_TILT.md` |
| `smci_keep_backtest.py` | SMCI floor overlay and DRAM live substitution. | `outputs/SMCI_KEEP_BACKTEST.md` |
| `exit_rule_comparison.py` | No-rebalance, downturn-exit, and GLD-vs-BIL comparison. | `outputs/EXIT_RULE_COMPARISON.md` |
| `cash_dip_reserve_backtest.py` | Cash reserve and dip-buy overlay tests. | `outputs/CASH_DIP_RESERVE_BACKTEST.md` |
| `current_1204_order_sheet.py` | Rebuilds the 12:04 screenshot GLD order sheet from committed cache and holdings. | `outputs/current_1204_exact_order_sheet_GLD_defensive.csv` |
| `nbis_redirect_sensitivity.py` | Tests lower NBIS floor/redirect and monthly cadence alternatives. | `outputs/NBIS_REDIRECT_SENSITIVITY.md` |
| `band_rebalance_aftertax.py` | Holdings-level after-tax simulator for full, monthly, and L1-band execution rules. | `outputs/BAND_REBALANCE_AFTERTAX.md` |
| `live_band_decision.py` | Live/current-holdings L1 band checker that prints HOLD/TRADE and order sheet. | terminal output |
| `strategy_comparison_charts.py` | Compares selected strategy against QQQ and buy-and-hold AI/semis brackets, with charts. | `outputs/STRATEGY_COMPARISON_CHARTS.md` |
| `buy_hold_entry_timing.py` | Tests lump-sum, DCA, pullback, and trend-entry rules for buy-and-hold baskets. | `outputs/BUY_HOLD_ENTRY_TIMING.md` |

## Final Strategy Files

The final user-selected strategy is documented in:

- `outputs/FINAL_NO_CASH_GLD_STRATEGY.md`
- `outputs/current_1204_exact_order_sheet_GLD_defensive.csv`
- `outputs/exit_rule_comparison_full_results.csv`
- `outputs/cash_dip_reserve_results.csv`
- `outputs/tomorrow_down_10_no_reserve_gld_actions.csv`
- `outputs/NBIS_REDIRECT_SENSITIVITY.md`
- `outputs/alternative_nbis_redirect_order_sheet.csv`
- `outputs/BAND_REBALANCE_AFTERTAX.md`
- `outputs/band_rebalance_aftertax_results.csv`
- `outputs/STRATEGY_COMPARISON_CHARTS.md`
- `outputs/strategy_comparison_full_window.png`
- `outputs/strategy_comparison_common_window.png`
- `outputs/strategy_comparison_drawdowns.png`
- `outputs/BUY_HOLD_ENTRY_TIMING.md`
- `outputs/buy_hold_entry_timing_3y_bars.png`
- `outputs/buy_hold_entry_timing_3y_win_rates.png`
- `outputs/buy_hold_entry_timing_current_basket.png`

## Important Caveats

- Fundamental data is a current snapshot, not point-in-time historical fundamentals.
- The universe includes current AI/semis winners, so survivorship/theme-selection bias is present.
- NBIS, GEV, SNDK, and DRAM do not provide clean full 10-year live histories.
- DRAM is a live substitution for the historical SNDK memory proxy.
- Taxes are modeled only in `band_rebalance_aftertax.py`; other CAGR tables are pre-tax.
- The after-tax simulator uses average-cost accounting and does not model lot selection, tax-loss harvesting, or personal estimated-tax timing.
