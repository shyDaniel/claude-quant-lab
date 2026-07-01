# NBIS Redirect Sensitivity

Date: 2026-07-01

## Why This Exists

Claude's audit correctly flagged that today's 26.45% NBIS weight is not mainly the explicit 25% floor. The base model's memory/storage exposure exceeds the 30% storage cap, and the selected `storage_excess_to_nbis=1.00` parameter redirects that excess into NBIS.

This file tests a less extreme variant: NBIS floor 15% and storage redirect 50%, while keeping QQQ, GLD, SMCI, DRAM substitution, storage cap, scoring, and trend rules otherwise unchanged.

## Results

| Strategy | CAGR | Sharpe | MaxDD | Worst 12m | Turnover | NBIS | Storage | GLD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| selected_weekly_floor25_redirect100 | 62.61% | 1.77 | -29.70% | -25.40% | 10.11x | 26.45% | 27.22% | 4.75% |
| alt_weekly_floor15_redirect50 | 60.93% | 1.76 | -29.70% | -25.40% | 10.20x | 20.73% | 27.22% | 4.75% |
| alt_monthly_floor15_redirect50 | 56.18% | 1.62 | -30.16% | -20.31% | 5.14x | 20.73% | 27.22% | 4.75% |

## Interpretation

- Selected weekly model: CAGR 62.61%, NBIS 26.45%, turnover 10.11x.
- Lower-redirect weekly model: CAGR 60.93%, NBIS 20.73%, turnover 10.20x.
- Lower-redirect monthly model: CAGR 56.18%, NBIS 20.73%, turnover 5.14x.

The lower-redirect variant gives up some backtested CAGR but reduces single-name NBIS concentration. That trade is small relative to the known survivorship, lookahead, tax, and short-history uncertainties.

## Alternative Weekly Target Weights

| ticker   |   target_weight |   target_value |   trade_dollars |   approx_shares_to_trade | action   |
|:---------|----------------:|---------------:|----------------:|-------------------------:|:---------|
| QQQ      |          0.2500 |     69681.5400 |        788.3400 |                   1.0871 | BUY      |
| NBIS     |          0.2073 |     57771.1407 |      11602.2307 |                  50.0086 | BUY      |
| MU       |          0.1981 |     55210.0790 |      27210.4690 |                  26.2390 | BUY      |
| NVDA     |          0.1099 |     30630.7645 |      10871.1545 |                  55.0226 | BUY      |
| DRAM     |          0.0742 |     20670.1261 |        245.7661 |                   3.7063 | BUY      |
| GLD      |          0.0475 |     13225.9510 |      13225.9510 |                  35.6879 | BUY      |
| GEV      |          0.0436 |     12138.5632 |      12138.5632 |                  10.7009 | BUY      |
| AMD      |          0.0393 |     10949.9955 |      10949.9955 |                  20.2448 | BUY      |
| SMCI     |          0.0303 |      8448.0000 |         93.0000 |                   3.3393 | BUY      |

## Files

- `outputs/nbis_redirect_sensitivity_results.csv`
- `outputs/nbis_redirect_sensitivity_order_sheets.csv`
- `outputs/alternative_nbis_redirect_order_sheet.csv`
