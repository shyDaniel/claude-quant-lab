# Catastrophe Gate Buy-and-Hold Sweep

Date: 2026-07-01

## Method

- Basket: equal-weight full-history AI/semis names with valid data at 2016-07-01.
- Tickers: `NVDA, AMD, AVGO, INTC, MU, MRVL, STX, ANET, SMCI`.
- Gate: hold the basket unless it closes more than threshold below its trailing 252-trading-day high; then switch to GLD.
- Re-entry: switch back when the basket is back within the same threshold of its trailing 252-trading-day high.
- Sweep: thresholds 10%, 15%, 20%, 25%; weekly and monthly checks.
- Taxes: lot-level synthetic-basket/GLD accounting with 50% ST tax, 33.1% LT tax, annual tax payment, and final liquidation tax.

## Results

| strategy           | pre_tax_cagr   | after_liq_cagr   | max_drawdown_pre_tax   | worst_12m_pre_tax   | after_tax_curve_max_drawdown   |   trades | end_pre_tax   | end_after_tax_after_liq   |
|:-------------------|:---------------|:-----------------|:-----------------------|:--------------------|:-------------------------------|---------:|:--------------|:--------------------------|
| Buy-hold EW-9      | 50.8%          | 45.0%            | -54.8%                 | -47.6%              | -54.8%                         |        0 | $16.78M       | $11.32M                   |
| weekly_gate_10pct  | 38.8%          | 22.6%            | -36.2%                 | -24.8%              | -51.4%                         |       58 | $7.34M        | $2.13M                    |
| weekly_gate_15pct  | 48.3%          | 32.3%            | -30.5%                 | -23.3%              | -38.8%                         |       34 | $14.21M       | $4.53M                    |
| weekly_gate_20pct  | 40.1%          | 28.6%            | -47.1%                 | -42.1%              | -51.5%                         |       24 | $8.04M        | $3.43M                    |
| weekly_gate_25pct  | 43.1%          | 31.1%            | -46.7%                 | -41.6%              | -52.7%                         |       16 | $9.97M        | $4.15M                    |
| monthly_gate_10pct | 38.8%          | 23.3%            | -31.5%                 | -24.4%              | -43.1%                         |       22 | $7.35M        | $2.25M                    |
| monthly_gate_15pct | 53.1%          | 37.9%            | -28.9%                 | -20.7%              | -36.7%                         |       12 | $19.52M       | $6.85M                    |
| monthly_gate_20pct | 45.8%          | 33.9%            | -44.7%                 | -39.4%              | -52.3%                         |        6 | $11.94M       | $5.11M                    |
| monthly_gate_25pct | 45.9%          | 34.1%            | -44.7%                 | -39.4%              | -52.3%                         |        6 | $12.05M       | $5.21M                    |

## 15% Monthly Gate Trade Log

| date       | action        | basket_drawdown_from_1y_high   | portfolio_value   |
|:-----------|:--------------|:-------------------------------|:------------------|
| 2018-10-31 | basket_to_gld | -23.4%                         | $0.68M            |
| 2019-02-28 | gld_to_basket | -14.7%                         | $0.60M            |
| 2019-05-31 | basket_to_gld | -19.2%                         | $0.57M            |
| 2019-06-28 | gld_to_basket | -9.5%                          | $0.61M            |
| 2020-02-28 | basket_to_gld | -16.4%                         | $0.71M            |
| 2020-04-30 | gld_to_basket | -9.3%                          | $0.76M            |
| 2022-01-31 | basket_to_gld | -19.5%                         | $1.64M            |
| 2023-03-31 | gld_to_basket | -4.7%                          | $1.46M            |
| 2024-08-30 | basket_to_gld | -17.6%                         | $3.83M            |
| 2024-09-30 | gld_to_basket | -14.6%                         | $4.03M            |
| 2025-01-31 | basket_to_gld | -16.4%                         | $3.10M            |
| 2025-05-30 | gld_to_basket | -13.5%                         | $3.63M            |

## Current Target Basket Extension

- Cached date: `2026-07-01`.
- EW-9 full-history basket vs 200dma: `41.6%`.
- Current target basket vs 200dma: `123.8%`.
- The EW-9 number is the one that matches Claude's `+41.6%`; the current target basket is more extended because it includes NBIS/SNDK/GEV and today's target weights.

## Interpretation

- Claude's corrected taxable-account conclusion is directionally right: buy-and-hold wins after liquidation against the gate in this taxable model.
- The 15% monthly gate improves pre-tax return and sharply reduces drawdown, but taxes turn that protection into an after-tax return drag.
- Weekly gates trade more often and are not clearly worth the added churn.
- In taxable, the gate is insurance. In a sheltered account, the same gate is much more attractive because the pre-tax result matters.
- The current target basket is extended versus its 200-day average in the cached data, so regret-control tranching is psychologically reasonable even though rolling entry tests usually favor lump sum.

## Charts

- `catastrophe_gate_curves.png`
- `catastrophe_gate_sweep.png`
