# Medium Transform Grid Search

This is the expanded but fast grid for cap smoothing/small-cap tilt and earnings transforms.

## Winners
- Best close-to-close: `size=sqrt_raw_cap|earn=square|mom=1.5|top=5|weekly|close`: CAGR 56.6%, Sharpe 1.67, MaxDD -31.1%, turnover 10.6x
- Best robust close-to-close: `size=sqrt_raw_cap|earn=square|mom=1.5|top=7|weekly|close`: CAGR 55.4%, Sharpe 1.66, MaxDD -31.4%, turnover 10.5x
- Best overnight: `size=barbell|earn=square|mom=1.5|top=5|weekly|overnight`: CAGR 46.8%, Sharpe 2.14, MaxDD -18.0%, turnover 11.5x

## Selected Best Weights
|      |    weight |
|:-----|----------:|
| MU   | 0.385044  |
| QQQ  | 0.25      |
| SNDK | 0.144157  |
| NVDA | 0.0836759 |
| STX  | 0.0539636 |
| BIL  | 0.05      |
| GEV  | 0.0331597 |
| MRVL | 0         |
| INTC | 0         |
| AMD  | 0         |
| VST  | 0         |
| CEG  | 0         |
| VRT  | 0         |
| NBIS | 0         |
| SMCI | 0         |
| AVGO | 0         |
| ANET | 0         |

## Selected Order Sheet
| strategy_id                                              | ticker   |   current_value |   target_value |   trade_dollars |   price |   approx_shares |
|:---------------------------------------------------------|:---------|----------------:|---------------:|----------------:|--------:|----------------:|
| size=sqrt_raw_cap|earn=square|mom=1.5|top=5|weekly|close | MU       |        26576.50 |      107321.84 |        80745.34 | 1032.28 |           78.22 |
| size=sqrt_raw_cap|earn=square|mom=1.5|top=5|weekly|close | QQQ      |        72839.00 |       69681.54 |        -3157.46 |  725.17 |           -4.35 |
| size=sqrt_raw_cap|earn=square|mom=1.5|top=5|weekly|close | SNDK     |            0.00 |       40180.27 |        40180.27 | 2032.22 |           19.77 |
| size=sqrt_raw_cap|earn=square|mom=1.5|top=5|weekly|close | NVDA     |        19955.00 |       23322.67 |         3367.68 |  197.58 |           17.04 |
| size=sqrt_raw_cap|earn=square|mom=1.5|top=5|weekly|close | STX      |            0.00 |       15041.06 |        15041.06 |  915.19 |           16.43 |
| size=sqrt_raw_cap|earn=square|mom=1.5|top=5|weekly|close | BIL      |            0.00 |       13936.31 |        13936.31 |   91.40 |          152.48 |
| size=sqrt_raw_cap|earn=square|mom=1.5|top=5|weekly|close | GEV      |            0.00 |        9242.46 |         9242.46 | 1134.35 |            8.15 |
| size=sqrt_raw_cap|earn=square|mom=1.5|top=5|weekly|close | CASH     |       102555.39 |           0.00 |      -102555.39 |  nan    |          nan    |
| size=sqrt_raw_cap|earn=square|mom=1.5|top=5|weekly|close | DRAM     |        20106.67 |           0.00 |       -20106.67 |  nan    |          nan    |
| size=sqrt_raw_cap|earn=square|mom=1.5|top=5|weekly|close | NBIS     |        28190.40 |           0.00 |       -28190.40 |  229.18 |         -123.01 |
| size=sqrt_raw_cap|earn=square|mom=1.5|top=5|weekly|close | SMCI     |         8448.00 |           0.00 |        -8448.00 |   27.65 |         -305.53 |

Chart: `medium_transform_grid_chart.png`
