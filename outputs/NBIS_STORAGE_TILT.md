# NBIS Conviction And Storage Cap Grid

Date: 2026-07-01

## Question

The previous optimizer placed very high weight in memory/storage names and very low weight in NBIS. This run treats NBIS conviction and storage concentration as explicit hyperparameters.

## Grid Tested

- Base strategy: sqrt raw market-cap, squared earnings score, 6-month momentum^1.5, top 7, weekly rebalance, close-to-close returns.
- NBIS floor: 0%, 5%, 7.5%, 10%, 12.5%, 15%, 20%, 25% of the whole account.
- Storage cap: 30%, 35%, 40%, 45%, 50%, 55%, or uncapped 70% of the whole account across MU/SNDK/STX.
- NBIS activation policy: trend-gated or tradable-with-history.
- Storage excess redirect: 0%, 25%, 50%, 75%, or 100% of storage-cap excess directed to NBIS.

## Key Results

- Baseline robust optimizer: CAGR 55.4%, Sharpe 1.66, MaxDD -31.4%, current NBIS 2.6%, current storage 53.8%.
- Strict audited NBIS tilt: `nbis_floor=0.100|storage_cap=0.450|policy=trend_gated|storage_excess_to_nbis=0.00|close`: CAGR 54.3%, Sharpe 1.66, MaxDD -31.4%, current NBIS 10.0%, current storage 45.0%.
- Best raw overlay: `nbis_floor=0.250|storage_cap=0.300|policy=tradable|storage_excess_to_nbis=1.00|close`: CAGR 55.9%, Sharpe 1.67, MaxDD -31.2%, current NBIS 26.5%, current storage 30.0%.
- Selected conviction overlay: `nbis_floor=0.250|storage_cap=0.300|policy=tradable|storage_excess_to_nbis=1.00|close`: CAGR 55.9%, Sharpe 1.67, MaxDD -31.2%, current NBIS 26.5%, current storage 30.0%.

## NBIS Data Caveat

NBIS clean price history in this data starts on 2024-10-21, when Nasdaq trading resumed under the Nebius name. So the NBIS overlay is not a pure 10-year NBIS proof. It is a current-conviction overlay tested inside a 10-year framework.

## Top 15 By CAGR

| strategy_id                                                                          |   cagr |   sharpe |   max_drawdown |   worst_12m |   turnover |   current_nbis_weight |   current_storage_weight |
|:-------------------------------------------------------------------------------------|-------:|---------:|---------------:|------------:|-----------:|----------------------:|-------------------------:|
| nbis_floor=0.250|storage_cap=0.300|policy=tradable|storage_excess_to_nbis=1.00|close | 0.5595 |   1.6666 |        -0.3125 |     -0.2396 |    10.2887 |                0.2645 |                   0.3000 |
| nbis_floor=0.250|storage_cap=0.300|policy=tradable|storage_excess_to_nbis=0.75|close | 0.5592 |   1.6673 |        -0.3125 |     -0.2396 |    10.2866 |                0.2609 |                   0.3000 |
| nbis_floor=0.250|storage_cap=0.300|policy=tradable|storage_excess_to_nbis=0.50|close | 0.5589 |   1.6680 |        -0.3125 |     -0.2396 |    10.2852 |                0.2573 |                   0.3000 |
| nbis_floor=0.200|storage_cap=0.350|policy=tradable|storage_excess_to_nbis=1.00|close | 0.5586 |   1.6754 |        -0.3130 |     -0.2410 |    10.3528 |                0.2145 |                   0.3500 |
| nbis_floor=0.250|storage_cap=0.300|policy=tradable|storage_excess_to_nbis=0.25|close | 0.5586 |   1.6687 |        -0.3125 |     -0.2396 |    10.2840 |                0.2536 |                   0.3000 |
| nbis_floor=0.125|storage_cap=0.400|policy=tradable|storage_excess_to_nbis=1.00|close | 0.5585 |   1.6824 |        -0.3136 |     -0.2419 |    10.3960 |                0.1645 |                   0.4000 |
| nbis_floor=0.200|storage_cap=0.350|policy=tradable|storage_excess_to_nbis=0.75|close | 0.5583 |   1.6761 |        -0.3130 |     -0.2410 |    10.3507 |                0.2109 |                   0.3500 |
| nbis_floor=0.250|storage_cap=0.300|policy=tradable|storage_excess_to_nbis=0.00|close | 0.5583 |   1.6693 |        -0.3125 |     -0.2396 |    10.2834 |                0.2500 |                   0.3000 |
| nbis_floor=0.200|storage_cap=0.350|policy=tradable|storage_excess_to_nbis=0.50|close | 0.5580 |   1.6767 |        -0.3130 |     -0.2410 |    10.3493 |                0.2073 |                   0.3500 |
| nbis_floor=0.075|storage_cap=0.450|policy=tradable|storage_excess_to_nbis=1.00|close | 0.5580 |   1.6802 |        -0.3140 |     -0.2422 |    10.4329 |                0.1145 |                   0.4500 |
| nbis_floor=0.150|storage_cap=0.400|policy=tradable|storage_excess_to_nbis=1.00|close | 0.5580 |   1.6798 |        -0.3136 |     -0.2419 |    10.3902 |                0.1645 |                   0.4000 |
| nbis_floor=0.125|storage_cap=0.400|policy=tradable|storage_excess_to_nbis=0.75|close | 0.5579 |   1.6830 |        -0.3136 |     -0.2419 |    10.3927 |                0.1547 |                   0.4000 |
| nbis_floor=0.200|storage_cap=0.350|policy=tradable|storage_excess_to_nbis=0.25|close | 0.5577 |   1.6772 |        -0.3130 |     -0.2410 |    10.3481 |                0.2036 |                   0.3500 |
| nbis_floor=0.150|storage_cap=0.400|policy=tradable|storage_excess_to_nbis=0.75|close | 0.5576 |   1.6803 |        -0.3136 |     -0.2419 |    10.3881 |                0.1609 |                   0.4000 |
| nbis_floor=0.050|storage_cap=0.500|policy=tradable|storage_excess_to_nbis=1.00|close | 0.5576 |   1.6767 |        -0.3140 |     -0.2424 |    10.4540 |                0.0645 |                   0.5000 |

## Selected Current Weights

| Unnamed: 0   |   weight |
|:-------------|---------:|
| NBIS         |   0.2645 |
| QQQ          |   0.2500 |
| MU           |   0.1981 |
| NVDA         |   0.0772 |
| SNDK         |   0.0742 |
| BIL          |   0.0500 |
| GEV          |   0.0306 |
| STX          |   0.0278 |
| AMD          |   0.0276 |
| MRVL         |   0.0000 |
| VST          |   0.0000 |
| CEG          |   0.0000 |
| VRT          |   0.0000 |
| INTC         |   0.0000 |
| SMCI         |   0.0000 |
| AVGO         |   0.0000 |
| ANET         |   0.0000 |

## Selected Order Sheet

| strategy_id                                                                          | ticker   |   current_value |   target_value |   trade_dollars |   price |   approx_shares |   target_weight |
|:-------------------------------------------------------------------------------------|:---------|----------------:|---------------:|----------------:|--------:|----------------:|----------------:|
| nbis_floor=0.250|storage_cap=0.300|policy=tradable|storage_excess_to_nbis=1.00|close | NBIS     |        28190.40 |       73733.36 |        45542.96 |  229.18 |          198.72 |            0.26 |
| nbis_floor=0.250|storage_cap=0.300|policy=tradable|storage_excess_to_nbis=1.00|close | QQQ      |        72839.00 |       69681.54 |        -3157.46 |  725.17 |           -4.35 |            0.25 |
| nbis_floor=0.250|storage_cap=0.300|policy=tradable|storage_excess_to_nbis=1.00|close | MU       |        26576.50 |       55210.08 |        28633.58 | 1032.28 |           27.74 |            0.20 |
| nbis_floor=0.250|storage_cap=0.300|policy=tradable|storage_excess_to_nbis=1.00|close | NVDA     |        19955.00 |       21529.11 |         1574.11 |  197.58 |            7.97 |            0.08 |
| nbis_floor=0.250|storage_cap=0.300|policy=tradable|storage_excess_to_nbis=1.00|close | SNDK     |            0.00 |       20670.13 |        20670.13 | 2032.22 |           10.17 |            0.07 |
| nbis_floor=0.250|storage_cap=0.300|policy=tradable|storage_excess_to_nbis=1.00|close | BIL      |            0.00 |       13936.31 |        13936.31 |   91.40 |          152.48 |            0.05 |
| nbis_floor=0.250|storage_cap=0.300|policy=tradable|storage_excess_to_nbis=1.00|close | GEV      |            0.00 |        8531.70 |         8531.70 | 1134.35 |            7.52 |            0.03 |
| nbis_floor=0.250|storage_cap=0.300|policy=tradable|storage_excess_to_nbis=1.00|close | STX      |            0.00 |        7737.64 |         7737.64 |  915.19 |            8.45 |            0.03 |
| nbis_floor=0.250|storage_cap=0.300|policy=tradable|storage_excess_to_nbis=1.00|close | AMD      |            0.00 |        7696.30 |         7696.30 |  540.88 |           14.23 |            0.03 |
| nbis_floor=0.250|storage_cap=0.300|policy=tradable|storage_excess_to_nbis=1.00|close | CASH     |       102555.39 |           0.00 |      -102555.39 |  nan    |          nan    |            0.00 |
| nbis_floor=0.250|storage_cap=0.300|policy=tradable|storage_excess_to_nbis=1.00|close | DRAM     |        20106.67 |           0.00 |       -20106.67 |  nan    |          nan    |            0.00 |
| nbis_floor=0.250|storage_cap=0.300|policy=tradable|storage_excess_to_nbis=1.00|close | SMCI     |         8448.00 |           0.00 |        -8448.00 |   27.65 |         -305.53 |            0.00 |

## Interpretation

The storage-heavy result is not a generic AI result. It is mostly a memory-cycle result. NBIS can be made a real position without breaking the historical backtest, but the evidence quality is lower than for long-history names because NBIS has only clean post-resumption trading history.

My practical preference for a return-seeking account is the selected conviction overlay if you really believe the NBIS thesis. The stricter audited version is the 10% NBIS / 45% storage-cap rule. The aggressive version is the 25%+ NBIS / 30% storage-cap rule.

Chart: `nbis_storage_tilt_chart.png`
