# SMCI Keep Backtest

Date: 2026-07-01

## Question

The user wants to keep SMCI. This tests SMCI as an explicit floor layered on top of the aggressive NBIS + storage-cap strategy.

## Method

- Base: aggressive NBIS/storage strategy from `NBIS_STORAGE_TILT.md`.
- SMCI floors tested: 0%, 2.5%, current account weight, 5%, 7.5%, 10%, 15%, 20%.
- Funding order: remove STX first, then BIL/cash, then smaller AI positions if needed.
- Historical backtest still uses SNDK as the memory-stock proxy because DRAM ETF history is too short for a real long backtest.
- Live order sheet maps the SNDK slot to the user's existing DRAM ETF position.

## Results

- No-SMCI baseline: CAGR 55.9%, Sharpe 1.67, MaxDD -31.2%.
- Current-size SMCI floor: `smci_floor=0.0303|policy=tradable|on_aggressive_nbis_storage|close`: CAGR 56.6%, Sharpe 1.66, MaxDD -30.9%.
- Best raw SMCI floor: `smci_floor=0.1000|policy=tradable|on_aggressive_nbis_storage|close`: CAGR 58.8%, Sharpe 1.64, MaxDD -29.5%.

## Full Grid

| strategy_id                                                           |   cagr |   sharpe |   max_drawdown |   worst_12m |   turnover |   current_smci_weight |   current_stx_weight |   current_bil_weight |
|:----------------------------------------------------------------------|-------:|---------:|---------------:|------------:|-----------:|----------------------:|---------------------:|---------------------:|
| smci_floor=0.1000|policy=tradable|on_aggressive_nbis_storage|close    | 0.5881 |   1.6430 |        -0.2946 |     -0.1772 |     9.5952 |                0.1000 |               0.0000 |               0.0000 |
| smci_floor=0.0750|policy=tradable|on_aggressive_nbis_storage|close    | 0.5845 |   1.6515 |        -0.3017 |     -0.1942 |     9.8585 |                0.0750 |               0.0000 |               0.0028 |
| smci_floor=0.2000|policy=trend_gated|on_aggressive_nbis_storage|close | 0.5839 |   1.6535 |        -0.2697 |     -0.2248 |    13.2904 |                0.0000 |               0.0278 |               0.0500 |
| smci_floor=0.1500|policy=tradable|on_aggressive_nbis_storage|close    | 0.5830 |   1.6041 |        -0.2953 |     -0.1403 |     8.9757 |                0.1500 |               0.0000 |               0.0000 |
| smci_floor=0.1500|policy=trend_gated|on_aggressive_nbis_storage|close | 0.5822 |   1.6606 |        -0.2798 |     -0.2363 |    12.5232 |                0.0000 |               0.0278 |               0.0500 |
| smci_floor=0.1000|policy=trend_gated|on_aggressive_nbis_storage|close | 0.5803 |   1.6660 |        -0.2968 |     -0.2413 |    11.8087 |                0.0000 |               0.0278 |               0.0500 |
| smci_floor=0.2000|policy=tradable|on_aggressive_nbis_storage|close    | 0.5783 |   1.5608 |        -0.3065 |     -0.1743 |     8.4881 |                0.2000 |               0.0000 |               0.0000 |
| smci_floor=0.0750|policy=trend_gated|on_aggressive_nbis_storage|close | 0.5756 |   1.6644 |        -0.3008 |     -0.2420 |    11.4446 |                0.0000 |               0.0278 |               0.0500 |
| smci_floor=0.0500|policy=tradable|on_aggressive_nbis_storage|close    | 0.5755 |   1.6592 |        -0.3073 |     -0.2094 |    10.0562 |                0.0500 |               0.0000 |               0.0278 |
| smci_floor=0.0500|policy=trend_gated|on_aggressive_nbis_storage|close | 0.5702 |   1.6688 |        -0.3035 |     -0.2395 |    11.0475 |                0.0000 |               0.0278 |               0.0500 |
| smci_floor=0.0303|policy=tradable|on_aggressive_nbis_storage|close    | 0.5660 |   1.6644 |        -0.3085 |     -0.2209 |    10.1085 |                0.0303 |               0.0000 |               0.0475 |
| smci_floor=0.0303|policy=trend_gated|on_aggressive_nbis_storage|close | 0.5652 |   1.6716 |        -0.3064 |     -0.2388 |    10.6896 |                0.0000 |               0.0278 |               0.0500 |
| smci_floor=0.0250|policy=tradable|on_aggressive_nbis_storage|close    | 0.5642 |   1.6655 |        -0.3089 |     -0.2245 |    10.1294 |                0.0250 |               0.0028 |               0.0500 |
| smci_floor=0.0250|policy=trend_gated|on_aggressive_nbis_storage|close | 0.5637 |   1.6712 |        -0.3072 |     -0.2392 |    10.6001 |                0.0000 |               0.0278 |               0.0500 |
| smci_floor=0.0000|policy=trend_gated|on_aggressive_nbis_storage|close | 0.5595 |   1.6666 |        -0.3125 |     -0.2396 |    10.2887 |                0.0000 |               0.0278 |               0.0500 |
| smci_floor=0.0000|policy=tradable|on_aggressive_nbis_storage|close    | 0.5595 |   1.6666 |        -0.3125 |     -0.2396 |    10.2887 |                0.0000 |               0.0278 |               0.0500 |

## Live Order Sheet

| strategy_id                                 | ticker   |   current_value |   target_value |   trade_dollars |   price |   approx_shares |   target_weight |
|:--------------------------------------------|:---------|----------------:|---------------:|----------------:|--------:|----------------:|----------------:|
| aggressive_25_nbis_30_DRAM_keep_SMCI_no_STX | NBIS     |        28190.40 |       73733.36 |        45542.96 |  229.18 |          198.72 |            0.26 |
| aggressive_25_nbis_30_DRAM_keep_SMCI_no_STX | QQQ      |        72839.00 |       69681.54 |        -3157.46 |  725.17 |           -4.35 |            0.25 |
| aggressive_25_nbis_30_DRAM_keep_SMCI_no_STX | MU       |        26576.50 |       55210.08 |        28633.58 | 1032.28 |           27.74 |            0.20 |
| aggressive_25_nbis_30_DRAM_keep_SMCI_no_STX | NVDA     |        19955.00 |       21529.11 |         1574.11 |  197.58 |            7.97 |            0.08 |
| aggressive_25_nbis_30_DRAM_keep_SMCI_no_STX | DRAM     |        20106.67 |       20670.13 |          563.46 |   67.02 |            8.41 |            0.07 |
| aggressive_25_nbis_30_DRAM_keep_SMCI_no_STX | BIL      |            0.00 |       13225.95 |        13225.95 |   91.40 |          144.70 |            0.05 |
| aggressive_25_nbis_30_DRAM_keep_SMCI_no_STX | GEV      |            0.00 |        8531.70 |         8531.70 | 1134.35 |            7.52 |            0.03 |
| aggressive_25_nbis_30_DRAM_keep_SMCI_no_STX | SMCI     |         8448.00 |        8448.00 |            0.00 |   27.65 |            0.00 |            0.03 |
| aggressive_25_nbis_30_DRAM_keep_SMCI_no_STX | AMD      |            0.00 |        7696.30 |         7696.30 |  540.88 |           14.23 |            0.03 |
| aggressive_25_nbis_30_DRAM_keep_SMCI_no_STX | CASH     |       102555.39 |           0.00 |      -102555.39 |  nan    |          nan    |            0.00 |

## Interpretation

Keeping the current SMCI position did not hurt the backtest. It slightly improved CAGR and max drawdown versus the no-SMCI aggressive baseline. A 7.5%-10% SMCI floor had the highest raw CAGR in this specific test, but that is a bigger single-company execution/compliance bet.

My practical choice is to keep SMCI at the current roughly 3% account weight, remove STX, and keep DRAM as the memory/HBM basket instead of adding SNDK.

Chart: `smci_keep_backtest_chart.png`
