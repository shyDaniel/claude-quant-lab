# Buy-and-Hold Entry Timing Tests

Date: 2026-07-01

## Method

- Tests entry timing for buy-and-hold, not the weekly strategy.
- Rolling tests use every fifth trading day as a hypothetical start date.
- Full-history AI/semis bracket includes only names with data at 2016-07-01: `NVDA, AMD, AVGO, INTC, MU, MRVL, STX, ANET, SMCI`.
- Current target basket starts at `2025-02-13` because NBIS/GEV/SNDK history is short.
- Cash waiting earns 0% in these tests. That is conservative for DCA/waiting rules.
- A wait rule that never triggers deploys at its timeout, so no strategy hides in cash forever.

## 3-Year Rolling Starts: QQQ

| policy                   | median_cagr   | p10_cagr   | worst_cagr   | median_max_drawdown   | win_rate_vs_lump   |
|:-------------------------|:--------------|:-----------|:-------------|:----------------------|:-------------------|
| Lump sum now             | 20.1%         | 10.0%      | 6.9%         | -28.6%                | 0.0%               |
| DCA 3m                   | 19.0%         | 9.2%       | 5.9%         | -28.6%                | 27.6%              |
| DCA 6m                   | 18.2%         | 8.2%       | 4.6%         | -28.6%                | 20.5%              |
| DCA 12m                  | 17.0%         | 5.6%       | 2.3%         | -28.6%                | 19.3%              |
| 50% now + DCA 6m         | 18.7%         | 9.1%       | 6.1%         | -28.2%                | 17.0%              |
| 70% now + buy 10% dip/6m | 18.5%         | 10.0%      | 7.0%         | -28.6%                | 42.3%              |
| Wait 5% dip/3m           | 18.2%         | 8.8%       | 4.0%         | -28.6%                | 40.3%              |
| Wait 10% dip/6m          | 16.1%         | 7.9%       | 4.0%         | -28.6%                | 42.3%              |
| Wait 20% dip/12m         | 16.4%         | 1.4%       | -2.2%        | -28.6%                | 44.3%              |
| Trend entry 100d         | 19.2%         | 9.8%       | 6.9%         | -28.6%                | 3.4%               |
| Buy lower: below 100d/6m | 18.2%         | 10.3%      | 4.5%         | -28.6%                | 44.0%              |

## 3-Year Rolling Starts: Full-History AI/Semis

| policy                   | median_cagr   | p10_cagr   | worst_cagr   | median_max_drawdown   | win_rate_vs_lump   |
|:-------------------------|:--------------|:-----------|:-------------|:----------------------|:-------------------|
| Lump sum now             | 44.0%         | 32.5%      | 21.3%        | -42.0%                | 0.0%               |
| DCA 3m                   | 42.4%         | 30.4%      | 18.9%        | -42.0%                | 27.3%              |
| DCA 6m                   | 40.6%         | 27.4%      | 16.6%        | -42.0%                | 20.5%              |
| DCA 12m                  | 38.9%         | 21.4%      | 10.1%        | -42.0%                | 17.3%              |
| 50% now + DCA 6m         | 42.3%         | 29.7%      | 19.2%        | -41.6%                | 17.9%              |
| 70% now + buy 10% dip/6m | 43.3%         | 32.1%      | 20.4%        | -42.0%                | 41.5%              |
| Wait 5% dip/3m           | 43.2%         | 33.0%      | 12.6%        | -42.0%                | 52.6%              |
| Wait 10% dip/6m          | 43.2%         | 26.0%      | 12.2%        | -42.0%                | 41.5%              |
| Wait 20% dip/12m         | 36.3%         | 13.8%      | 3.3%         | -42.0%                | 25.3%              |
| Trend entry 100d         | 43.3%         | 31.0%      | 21.3%        | -42.0%                | 2.8%               |
| Buy lower: below 100d/6m | 41.9%         | 25.8%      | 15.8%        | -42.0%                | 32.7%              |

## Current Target Basket: Single Common Window

| policy                   | cagr   | max_drawdown   | end_value   | beats_lump   |
|:-------------------------|:-------|:---------------|:------------|:-------------|
| Lump sum now             | 372.5% | -35.7%         | $2.34M      | False        |
| DCA 3m                   | 426.2% | -22.5%         | $2.71M      | True         |
| DCA 6m                   | 377.1% | -22.5%         | $2.37M      | True         |
| DCA 12m                  | 282.7% | -22.5%         | $1.75M      | False        |
| 50% now + DCA 6m         | 368.9% | -22.4%         | $2.31M      | False        |
| 70% now + buy 10% dip/6m | 377.0% | -33.1%         | $2.37M      | True         |
| Wait 5% dip/3m           | 363.7% | -31.4%         | $2.28M      | False        |
| Wait 10% dip/6m          | 387.4% | -28.5%         | $2.44M      | True         |
| Wait 20% dip/12m         | 421.2% | -25.6%         | $2.67M      | True         |
| Trend entry 100d         | 320.9% | -22.5%         | $1.99M      | False        |
| Buy lower: below 100d/6m | 282.1% | -22.5%         | $1.75M      | False        |

## Interpretation

- Lump-sum buy-and-hold is the hardest entry rule to beat in upward-drifting assets.
- DCA and waiting rules can reduce regret/drawdown, but they usually lose median CAGR.
- Waiting for a 10-20% dip is especially costly when the dip does not arrive quickly.
- If choosing buy-and-hold for the current AI basket, the model evidence favors buying now or mostly now, not waiting for a perfect dip.
- The honest reason to use band strategy instead of buy-and-hold is not higher after-tax return versus every AI basket; it is a rule-based attempt to cap drawdown/regime risk.

## Charts

- `buy_hold_entry_timing_3y_bars.png`
- `buy_hold_entry_timing_3y_win_rates.png`
- `buy_hold_entry_timing_current_basket.png`
