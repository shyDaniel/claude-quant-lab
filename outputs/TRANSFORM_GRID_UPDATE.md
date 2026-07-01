# Transform Grid Update

Date: 2026-07-01

## What Changed

The previous grid only tested a few cap/earnings exponents. This update tested explicit market-cap smoothing and small-cap tilt transforms:

- equal weight,
- cap rank,
- sqrt cap rank,
- log cap,
- sqrt raw market cap,
- small-cap tilt,
- barbell large/small-cap tilt,
- earnings transforms: none, sqrt, linear, square, growth-only,
- momentum powers: 0.0, 0.5, 1.0, 1.5,
- top-N baskets: 5, 7, 10, 12,
- weekly/monthly rebalance,
- close-to-close, overnight, intraday timing.

## Result

The best close-to-close strategy was:

`size=sqrt_raw_cap | earn=square | momentum=1.5 | top=5 | weekly | close`

10-year result:

- CAGR: 56.6%
- Sharpe: 1.67
- Max drawdown: -31.1%
- Turnover: 10.6x/year

Best robust version:

`size=sqrt_raw_cap | earn=square | momentum=1.5 | top=7 | weekly | close`

10-year result:

- CAGR: 55.4%
- Sharpe: 1.66
- Max drawdown: -31.4%
- Turnover: 10.5x/year

## Interpretation

Your intuition was right that plain market-cap weighting is not ideal. The best result did **not** use raw cap weighting and did **not** use pure equal weight.

The winning transform is **sqrt raw market cap**, which is a compromise:

- larger companies get more weight than in equal-weight,
- smaller growth companies still matter much more than in raw cap-weighting,
- concentration is reduced versus pure market cap.

Earnings mattered: the winner used **earnings score squared**, meaning it heavily rewards names with the strongest current earnings/growth profile.

Momentum mattered: the winner used **6-month momentum^1.5**, meaning it strongly favors the names already moving best.

## Close-To-Close Meaning

Close-to-close means:

> measure return from one trading day's closing price to the next trading day's closing price.

Example:

- Monday 4:00pm close: $100
- Tuesday 4:00pm close: $110
- close-to-close return = +10%

It includes both:

- overnight move: Monday close -> Tuesday open,
- intraday move: Tuesday open -> Tuesday close.

In this backtest:

- `close` = close-to-close, holding through both overnight and intraday,
- `overnight` = prior close to next open only,
- `intraday` = open to close only.

The timing test found:

- close-to-close had the highest total return,
- overnight had the highest Sharpe / cleaner risk,
- intraday was much weaker.

Practical implication:

**Do not chase the morning open. Prefer buying near the close or staging buys late in the day.**

## Best Raw Current Weights

| Ticker | Weight |
|---|---:|
| MU | 38.5% |
| QQQ | 25.0% |
| SNDK | 14.4% |
| NVDA | 8.4% |
| STX | 5.4% |
| BIL/cash | 5.0% |
| GEV | 3.3% |

This is the mathematically best raw backtest, but it is extremely concentrated in MU.

## Best Robust Current Weights

| Ticker | Weight |
|---|---:|
| MU | 35.5% |
| QQQ | 25.0% |
| SNDK | 13.3% |
| NVDA | 7.7% |
| BIL/cash | 5.0% |
| STX | 5.0% |
| GEV | 3.1% |
| AMD | 2.8% |
| NBIS | 2.6% |

Even the robust version is still very MU-heavy because current fundamentals and momentum heavily favor MU.

## My Actual Recommendation

If following the optimized return-seeking model strictly:

Use the **best robust top-7 version**, not the top-5 raw winner.

Reason: top-5 only adds about +1.2% CAGR but concentrates even more in MU. The top-7 version keeps almost all of the return while adding a little more breadth.

## Key Caveat

This grid uses current market cap and current earnings data as static weights. That creates lookahead bias. The backtest answers:

> Given today's information, what weighting scheme would have worked best historically?

It does **not** prove the exact weighting rule was knowable 10 years ago.

## Research Notes

- Equal weighting is known to create a smaller-cap tilt.
- Square-root market-cap weighting is used as a way to reduce concentration while retaining size/liquidity information.
- Fundamental indexing weights by economic measures rather than price alone.
