# Cash Reserve Dip-Buy Backtest

Date: 2026-07-01

## What Was Tested

- Baseline: current weekly GLD-defensive strategy.
- Static cash reserves: 10%, 15%, 20% cash, with GLD kept as the gold sleeve.
- Dynamic dip reserves: keep a cash reserve, then deploy one-third/two-thirds/all of it when the equity sleeve falls below recent highs.
- Refill rule: when the drawdown recovers, the weekly rebalance trims back into the cash reserve.

## Top Results

| strategy                                              |   cagr |   sharpe |   max_drawdown |   worst_12m |   turnover |   current_cash_weight |   current_gld_weight |   current_equity_weight |
|:------------------------------------------------------|-------:|---------:|---------------:|------------:|-----------:|----------------------:|---------------------:|------------------------:|
| no_cash_reserve_GLD                                   | 0.6261 |   1.7654 |        -0.2970 |     -0.2540 |    10.1085 |                0.0000 |               0.0475 |                  0.9525 |
| dip_cash_reserve_10_lookback_126_tranches_5_10_15     | 0.5706 |   1.7799 |        -0.2788 |     -0.2310 |    11.2058 |                0.0333 |               0.0475 |                  0.9192 |
| dip_cash_reserve_10_lookback_63_tranches_5_10_15      | 0.5687 |   1.7792 |        -0.2788 |     -0.2301 |    11.2670 |                0.0333 |               0.0475 |                  0.9192 |
| dip_cash_reserve_10_lookback_126_tranches_7p5_15_22p5 | 0.5663 |   1.7851 |        -0.2737 |     -0.2250 |    10.8269 |                0.0667 |               0.0475 |                  0.8859 |
| dip_cash_reserve_10_lookback_63_tranches_7p5_15_22p5  | 0.5643 |   1.7826 |        -0.2737 |     -0.2261 |    10.5008 |                0.0667 |               0.0475 |                  0.8859 |
| dip_cash_reserve_10_lookback_21_tranches_5_10_15      | 0.5638 |   1.7747 |        -0.2746 |     -0.2317 |    11.1217 |                0.0333 |               0.0475 |                  0.9192 |
| dip_cash_reserve_10_lookback_126_tranches_10_20_30    | 0.5602 |   1.7763 |        -0.2718 |     -0.2314 |    10.1960 |                0.0667 |               0.0475 |                  0.8859 |
| dip_cash_reserve_10_lookback_21_tranches_7p5_15_22p5  | 0.5598 |   1.7759 |        -0.2685 |     -0.2278 |    10.3009 |                0.0667 |               0.0475 |                  0.8859 |
| dip_cash_reserve_10_lookback_63_tranches_10_20_30     | 0.5596 |   1.7762 |        -0.2718 |     -0.2322 |    10.2479 |                0.0667 |               0.0475 |                  0.8859 |
| dip_cash_reserve_10_lookback_21_tranches_10_20_30     | 0.5579 |   1.7764 |        -0.2668 |     -0.2289 |    10.1403 |                0.0667 |               0.0475 |                  0.8859 |
| static_cash_reserve_10_pro_rata                       | 0.5553 |   1.7654 |        -0.2703 |     -0.2297 |     9.0976 |                0.1000 |               0.0427 |                  0.8573 |
| static_cash_reserve_10                                | 0.5534 |   1.7717 |        -0.2615 |     -0.2324 |     9.5567 |                0.1000 |               0.0475 |                  0.8525 |
| dip_cash_reserve_15_lookback_126_tranches_5_10_15     | 0.5430 |   1.7871 |        -0.2696 |     -0.2193 |    11.7603 |                0.0500 |               0.0475 |                  0.9025 |
| dip_cash_reserve_15_lookback_63_tranches_5_10_15      | 0.5403 |   1.7861 |        -0.2696 |     -0.2181 |    11.8516 |                0.0500 |               0.0475 |                  0.9025 |
| dip_cash_reserve_15_lookback_126_tranches_7p5_15_22p5 | 0.5366 |   1.7957 |        -0.2619 |     -0.2103 |    11.1922 |                0.1000 |               0.0475 |                  0.8525 |
| dip_cash_reserve_15_lookback_63_tranches_7p5_15_22p5  | 0.5337 |   1.7918 |        -0.2619 |     -0.2121 |    10.6985 |                0.1000 |               0.0475 |                  0.8525 |
| dip_cash_reserve_15_lookback_21_tranches_5_10_15      | 0.5330 |   1.7788 |        -0.2632 |     -0.2205 |    11.6319 |                0.0500 |               0.0475 |                  0.9025 |
| dip_cash_reserve_15_lookback_126_tranches_10_20_30    | 0.5277 |   1.7818 |        -0.2590 |     -0.2201 |    10.2406 |                0.1000 |               0.0475 |                  0.8525 |
| dip_cash_reserve_15_lookback_21_tranches_7p5_15_22p5  | 0.5270 |   1.7808 |        -0.2555 |     -0.2146 |    10.3976 |                0.1000 |               0.0475 |                  0.8525 |
| dip_cash_reserve_15_lookback_63_tranches_10_20_30     | 0.5268 |   1.7815 |        -0.2590 |     -0.2213 |    10.3181 |                0.1000 |               0.0475 |                  0.8525 |

## Selected Practical Reserve

`dip_cash_reserve_10_lookback_63_tranches_5_10_15`: CAGR 56.9%, Sharpe 1.78, MaxDD -27.9%, current cash 3.3%.

## Tomorrow -10% Scenario

- No cash reserve: only about $1.3k gets bought, funded by trimming GLD.
- 10% dynamic reserve: about $10.5k gets bought, funded mostly from remaining cash plus a small GLD trim.
- 15% dynamic reserve: about $15.1k gets bought, but the long-run CAGR hit is larger.

## Interpretation

Cash reserve lowered long-run CAGR because this is a high-return AI/semis strategy, but it materially improves your ability to buy a sudden dip without selling winners or GLD.

The practical compromise is 10%-15% cash, not 20%. A 20% reserve gives more psychological comfort but meaningfully reduces compounding.

Chart: `cash_dip_reserve_chart.png`
