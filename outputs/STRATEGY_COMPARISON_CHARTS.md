# Strategy Comparison Charts

Date: 2026-07-01

## What This Compares

- Full window: selected ALT 20% L1 band strategy versus QQQ and an equal-weight buy-and-hold basket of AI/semis names with full data from 2016-07-01.
- Common window: selected ALT 20% L1 band strategy versus buy-and-hold of the current target basket from 2025-02-13, the first date all current target names/proxies have data.
- Current basket uses SNDK as the historical memory proxy for live DRAM.
- Strategy after-tax curve uses annual 50% short-term tax payments deducted from portfolio value; liquidation uses the same 50% short-term rate.
- Buy-and-hold curves are shown pre-liquidation, with an after-liquidation column using 33.1% long-term tax on gains.

## Full Window Metrics

| strategy                           | cagr   | after_liq_cagr   | max_drawdown   | worst_12m   | end_value   | after_liq_end_value   |   rebalances | turnover   | daily_vol   |
|:-----------------------------------|:-------|:-----------------|:---------------|:------------|:------------|:----------------------|-------------:|:-----------|:------------|
| ALT L1>20% pre-tax                 | 60.2%  |                  | -29.6%         | -26.7%      | $30.57M     |                       |          147 | 8.9x       | 29.8%       |
| ALT L1>20% after-tax               | 38.5%  | 35.5%            | -38.8%         | -33.1%      | $7.16M      | $5.75M                |          147 | 8.9x       | 33.0%       |
| QQQ buy-and-hold                   | 21.9%  | 17.8%            | -35.1%         | -34.8%      | $2.00M      | $1.43M                |            0 | 0.0x       | 22.4%       |
| Equal-weight full-history AI/semis | 50.8%  | 45.0%            | -54.8%         | -47.6%      | $16.78M     | $11.32M               |            0 | 0.0x       | 39.2%       |

Full-history equal-weight tickers: `NVDA, AMD, AVGO, INTC, MU, MRVL, STX, ANET, SMCI`.

## Common Current-Basket Window Metrics

| strategy                          | cagr   | after_liq_cagr   | max_drawdown   | worst_12m   | end_value   | after_liq_end_value   |   rebalances | turnover   | daily_vol   |
|:----------------------------------|:-------|:-----------------|:---------------|:------------|:------------|:----------------------|-------------:|:-----------|:------------|
| ALT L1>20% strategy               | 141.3% |                  | -23.9%         | 87.3%       | $0.93M      |                       |           28 | 8.4x       | 41.2%       |
| Buy-hold current target basket    | 370.4% | 266.0%           | -35.7%         | 210.0%      | $2.34M      | $1.66M                |            0 | 0.0x       | 61.4%       |
| Equal-weight current target names | 415.5% | 299.2%           | -32.5%         | 233.8%      | $2.65M      | $1.86M                |            0 | 0.0x       | 62.3%       |
| QQQ buy-and-hold                  | 25.3%  | 17.2%            | -22.8%         | 12.5%       | $0.38M      | $0.35M                |            0 | 0.0x       | 23.2%       |

## Interpretation

- Versus QQQ: yes. The selected strategy beats QQQ both pre-tax and after liquidation in this cached-data framework.
- Versus a full-history equal-weight AI/semis buy-and-hold bracket: pre-tax yes, after-tax no. Buy-and-hold's tax deferral remains powerful.
- Versus buy-and-hold of the exact current target basket: no on the short common window. The final winners exploded during that specific period.
- The current-basket buy-and-hold result is not a 10-year proof; it is the exact survivorship problem the audit flagged.
- The strategy's claimed edge is not magic asset selection alone. It comes from owning a biased AI/semis universe plus trend gates, GLD routing, and rebalance discipline. The universe choice remains the dominant bias.

## Charts

- `strategy_comparison_full_window.png`
- `strategy_comparison_common_window.png`
- `strategy_comparison_drawdowns.png`
