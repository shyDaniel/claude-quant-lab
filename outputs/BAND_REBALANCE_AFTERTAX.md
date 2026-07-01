# Band Rebalance After-Tax Backtest

Date: 2026-07-01

## Method

- Base strategy: post-audit ALT model, `nbis_floor=15%`, `storage_excess_to_nbis=50%`, no cash, GLD defensive sleeve.
- Simulation: holdings-level close-to-close accounting with drift, average cost basis, realized gains, annual tax, loss carryforward, and 10 bps trading cost.
- Tax assumption: 50% short-term tax on annual net realized gains and strategy liquidation gains; QQQ buy-and-hold liquidation uses 33.1% long-term tax.
- Annual tax payments are deducted from portfolio value pro rata. Lot-level loss harvesting is not modeled.

## Key Results

| Strategy | Pre-tax CAGR | After-tax pre-liquidation | After liquidation | MaxDD after tax | Rebalances | True turnover |
|---|---:|---:|---:|---:|---:|---:|
| ALT weekly full rebalance | 60.3% | 36.8% | 34.5% | -39.3% | 523 | 11.0x |
| ALT weekly L1>10% | 60.4% | 37.7% | 35.0% | -38.5% | 268 | 10.1x |
| ALT weekly L1>15% | 59.5% | 37.6% | 34.9% | -38.8% | 189 | 9.4x |
| ALT weekly L1>20% | 60.2% | 38.5% | 35.5% | -38.8% | 147 | 8.9x |
| ALT weekly L1>25% | 61.4% | 39.4% | 36.3% | -39.1% | 126 | 8.5x |
| ALT weekly L1>30% | 60.6% | 39.4% | 35.8% | -37.8% | 106 | 8.0x |
| ALT monthly full rebalance | 56.5% | 36.7% | 33.6% | -41.3% | 121 | 5.6x |
| 70% ALT / 30% extra QQQ, L1>10% | 48.1% | 31.8% | 29.1% | -37.3% | 205 | 6.7x |
| 50% ALT / 50% extra QQQ, L1>10% | 40.1% | 28.5% | 25.5% | -37.2% | 160 | 4.6x |
| QQQ buy-and-hold | 21.9% | 21.9% | 17.8% | -35.1% | 0 | 0.0x |

## Selected Execution Rule

Selected: `ALT weekly L1>20%`. It produced 35.5% after-liquidation CAGR with 147 rebalances and 8.9x true turnover.

Rule:

```text
Every weekly signal date:
1. Recompute target weights.
2. Compute current drifted weights from live market values.
3. L1 drift = sum(abs(current_weight - target_weight)) across all holdings.
4. If L1 <= 0.20: hold.
5. If L1 > 0.20: fully rebalance to target weights near the close.
```

Monthly full rebalancing lowered turnover, but it also lowered after-tax results in this simulation. The 20% band kept weekly signal responsiveness while avoiding many small taxable trades.

The 25% band is slightly higher in this exact rerun; treat that as threshold-selection noise, not a reason to chase precision. The 20% band is the selected round-number policy default.

## Files

- `work/band_rebalance_aftertax.py`
- `outputs/band_rebalance_aftertax_results.csv`
