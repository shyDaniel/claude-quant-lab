# Final No-Cash GLD Strategy

Date: 2026-07-01

## Decision

The selected model is the **no-cash-reserve, weekly-rebalanced, GLD-defensive AI/semis strategy**.

Plain English:

- Do not keep a cash sleeve.
- Keep QQQ as a 25% core.
- Put the rest into a concentrated AI/semis basket, with NBIS as a conviction floor.
- Use GLD as the defensive/overflow sleeve instead of BIL or cash.
- Keep SMCI at the current small position size.
- Use DRAM as the live memory/HBM bucket instead of buying SNDK.
- Rebalance weekly from target weights; this is not a daily panic-trading model.

This is the highest-CAGR variant from the tested framework. The tradeoff is that it gives up the psychological comfort of dry powder. If the portfolio drops sharply tomorrow, the model can only buy the dip by trimming GLD or overweight names.

This is rule-based research, not fiduciary advice or a guarantee.

## Current Target Weights

These are the live target weights for the user's current preference set: no cash, no BIL, GLD defensive sleeve, DRAM instead of SNDK, keep SMCI, keep NBIS conviction.

| Ticker | Target weight | Role |
|---|---:|---|
| NBIS | 26.4537% | Conviction AI infrastructure floor |
| QQQ | 25.0000% | Core Nasdaq-100 growth exposure |
| MU | 19.8080% | Memory/HBM cycle exposure |
| NVDA | 7.7241% | AI accelerator/platform exposure |
| DRAM | 7.4159% | Live substitute for historical SNDK memory slot |
| GLD | 4.7451% | Gold defensive/overflow sleeve |
| GEV | 3.0610% | AI power/electrification exposure |
| SMCI | 3.0309% | Keep-current-position server exposure |
| AMD | 2.7612% | AI/compute exposure |
| Cash | 0.0000% | No reserve |
| BIL | 0.0000% | Rejected defensive asset |
| SNDK | 0.0000% live | Historical proxy only; replaced by DRAM live |
| STX | 0.0000% | Removed to make room for SMCI |

Target weights sum to 100%.

## Current Order Sheet

Based on the user's 12:04 screenshot and total account value of $278,726.16. Use target weights if live quotes or buying power differ.

| Action | Ticker | Target value | Current value | Trade dollars | Approx shares |
|---|---:|---:|---:|---:|---:|
| Buy | NBIS | $73,733.36 | $46,168.91 | $27,564.45 | 118.81 |
| Buy | MU | $55,210.08 | $27,999.61 | $27,210.47 | 26.24 |
| Buy | GLD | $13,225.95 | $0.00 | $13,225.95 | 35.69 |
| Buy | GEV | $8,531.70 | $0.00 | $8,531.70 | 7.52 |
| Buy | AMD | $7,696.30 | $0.00 | $7,696.30 | 14.23 |
| Buy | NVDA | $21,529.11 | $19,759.61 | $1,769.50 | 8.96 |
| Buy | QQQ | $69,681.54 | $68,893.20 | $788.34 | 1.09 |
| Buy | DRAM | $20,670.13 | $20,424.36 | $245.77 | 3.71 |
| Buy | SMCI | $8,448.00 | $8,355.00 | $93.00 | 3.34 |

If the broker shows a different total account value, recalculate each target value as:

```text
target_dollars = total_account_value * target_weight
trade_dollars = target_dollars - current_position_value
```

Because this is the no-cash model, leftover buying power after execution should be near zero except for rounding and unsettled cash.

## Exact Quantitative Strategy

### Universe

The research universe is:

```text
NVDA, AMD, AVGO, INTC, MU, SNDK, MRVL, STX, ANET, VST, CEG, GEV, VRT, NBIS, SMCI, QQQ, GLD
```

Live substitutions and exclusions:

- `SNDK` is used as a historical memory-stock proxy because DRAM ETF history is too short.
- Live target uses `DRAM` instead of `SNDK`.
- `STX` is removed in the live version to keep SMCI.
- `BIL` is replaced by `GLD`.
- `AVGO` and `INTC` are in the tested universe, but their current target weight is 0% because the score/trend system did not select them today.

### Base Allocation

Before overlays:

```text
QQQ core weight = 25%
AI/semis sleeve = 70%
defensive/overflow sleeve = 5%
cash reserve = 0%
```

The 70% AI/semis sleeve is scored and normalized across the selected top names.

### Score Formula

Each rebalance date, each AI/semis ticker receives a raw score:

```text
raw_score = active_gate * size_score * earnings_score^2 * momentum_score
```

Where:

```text
size_score = sqrt(company_market_cap / median_universe_market_cap)

earnings_score =
    0.35 * percentile_rank(earnings_quarterly_growth)
  + 0.25 * percentile_rank(revenue_growth)
  + 0.20 * percentile_rank(profit_margins)
  + 0.10 * percentile_rank(return_on_equity)
  + 0.10 * percentile_rank(forward_or_trailing_eps)

momentum_score = percentile_rank(126_trading_day_total_return)^1.5
```

The selected hyperparameters are:

| Parameter | Selected value |
|---|---:|
| Size transform | `sqrt_raw_cap` |
| Earnings transform | `square` |
| Momentum lookback | 126 trading days |
| Momentum power | 1.5 |
| Top names | 7 |
| Rebalance cadence | Weekly |
| Return measurement | Close-to-close |

### Active Gate

A normal AI/semis name is eligible only when:

```text
price > 100_day_moving_average
and the name has at least 126 valid daily observations
and the equal-weight AI basket is above its 100_day_moving_average
```

If a normal name fails the gate, its raw score is 0 and its weight is routed to the defensive/overflow sleeve.

### Normalization

On each weekly rebalance date:

```text
1. Compute raw_score for every AI/semis name.
2. Keep the top 7 positive-scoring names.
3. Normalize their scores to sum to the 70% AI/semis sleeve.
4. Add the fixed 25% QQQ core.
5. Route unallocated/defensive weight to GLD.
```

### NBIS Conviction Overlay

The user is highly bullish on NBIS, so NBIS is handled as a conviction overlay:

```text
NBIS floor = 25% of account
NBIS activation policy = tradable_with_history
storage cap = 30% of account across MU/SNDK/STX in the historical model
storage excess redirect = 100% to NBIS when NBIS is active
```

This means NBIS does not need to be above its 100-day moving average to keep the floor. It needs to have enough valid trading history. That is an intentional conviction override, not something the pure optimizer discovered from 10 years of NBIS data.

### SMCI Keep Overlay

SMCI is kept at the user's current approximate account weight:

```text
SMCI floor = 3.0309% of account
SMCI activation policy = tradable_with_history
```

The funding order for the SMCI floor is:

```text
STX first, then BIL/defensive, then AMD, GEV, NVDA, MU, SNDK, NBIS
```

In the final live model, this removes STX and keeps SMCI.

## Buy And Sell Rules

### Rebalance Rule

Rebalance weekly, using the last trading day of the week. The backtest uses the daily adjusted close series, so the clean operational version is:

```text
After or near the weekly close:
1. Calculate the new target weights.
2. Calculate target dollars from current account value.
3. Buy underweight names.
4. Sell overweight names.
5. Keep cash at 0% except rounding.
```

Close-to-close means:

```text
daily_return = adjusted_close_today / adjusted_close_yesterday - 1
```

It is the return measurement mode in the backtest. It does not mean the model recomputes and rebalances every day.

### When To Buy

Buy when:

```text
target_dollars > current_position_value
```

The buy amount is:

```text
buy_dollars = target_dollars - current_position_value
```

Example: if NBIS dips while its model target remains 26.4537%, the strategy buys enough NBIS at the weekly rebalance to restore NBIS to the target weight, funded by trimming GLD and/or overweight positions.

### When To Sell

Sell when:

```text
target_dollars < current_position_value
```

The sell amount is:

```text
sell_dollars = current_position_value - target_dollars
```

For NBIS specifically, the model sells NBIS in these situations:

1. NBIS rallies enough that it becomes above its target weight, then the weekly rebalance trims it back.
2. The storage/score overlay no longer redirects enough weight to NBIS and the NBIS target falls toward the 25% floor.
3. NBIS loses valid tradable history or otherwise becomes ineligible in the data; then the conviction floor turns off and the base score determines target weight.
4. The user explicitly switches to the lower-drawdown variant where conviction floors obey the 100-day moving-average gate.

The selected model does **not** sell NBIS merely because it falls below the 100-day moving average. That hard-exit version was tested and rejected for the user's chosen return-maximizing objective.

### What Happens After A 10% Broad AI Dip

If all equity-like positions drop 10% tomorrow and GLD is flat, the no-cash model does not have much dry powder. It buys only about $1.26k of equities, funded by trimming GLD:

| Ticker | Trade after broad -10% shock |
|---|---:|
| Buy NBIS | $350 |
| Buy QQQ | $331 |
| Buy MU | $262 |
| Buy NVDA | $102 |
| Buy DRAM/SNDK proxy | $98 |
| Buy GEV | $40 |
| Buy SMCI | $40 |
| Buy AMD | $37 |
| Sell GLD | $1,260 |

This is the key tradeoff. No-cash maximized tested CAGR, but it is not a big dip-buying system.

## Backtest Data

### Price Data

Primary research data:

- Cached adjusted daily closes: `work/cache/grid_prices.csv`
- Cached adjusted daily opens: `work/cache/grid_open_prices.csv`
- Cached fundamentals: `work/cache/grid_fundamentals_raw.csv`
- Main grid scripts use yfinance/Yahoo-sourced data.
- GLD was fetched by the GLD exit-rule script and included in the final generated comparison outputs.

Data range in cached price file:

```text
2015-01-02 through 2026-07-01
```

Important ticker history limits:

| Ticker | First valid cached date | Note |
|---|---:|---|
| QQQ | 2015-01-02 | Full cached framework history |
| SMCI | 2015-01-02 | Full cached framework history |
| GEV | 2024-03-27 | Short public-company history |
| NBIS | 2024-10-21 | Clean post-resumption Nebius history only |
| SNDK | 2025-02-13 | Short historical proxy for memory slot |
| DRAM | Not full-history-tested | Used live instead of SNDK |

### Fundamental Data

The scoring grid uses a current fundamental snapshot:

```text
market_cap
earnings_quarterly_growth
revenue_growth
profit_margins
return_on_equity
forward_eps / trailing_eps
```

Major caveat: the fundamentals are **not point-in-time historical fundamentals**. This creates lookahead bias. The backtest answers:

```text
Given today's known company/fundamental profile, which weighting transform would have worked historically?
```

It does not prove that the same exact weights were knowable 10 years ago.

### Costs And Mechanics

Assumptions:

| Item | Assumption |
|---|---:|
| Transaction cost | 10 bps per dollar of turnover |
| Taxes | Not modeled in final CAGR tables |
| Margin | None |
| Options | None |
| Dividends | Adjusted-price data where available |
| Rebalance execution | Weekly target-weight rebalance |
| Daily return mode | Close-to-close unless otherwise stated |

## Backtest Results

### Main Long Framework Window

Window: `2016-07-01` to `2026-07-01`. Starting account value for end-value math: `$278,726.16`.

| Strategy | CAGR | Sharpe | Max drawdown | Worst 12m | Turnover | End value |
|---|---:|---:|---:|---:|---:|---:|
| Selected no-cash weekly GLD strategy | 62.61% | 1.77 | -29.70% | -25.40% | 10.11x | $35.55M |
| Same strategy with BIL defensive sleeve | 56.60% | 1.66 | -30.85% | -22.09% | 10.11x | $24.41M |
| QQQ buy-and-hold | 21.94% | 1.00 | -35.12% | -34.76% | 0.00x | $2.01M |
| BIL buy-and-hold | 2.19% | 8.01 | -0.26% | -0.13% | 0.00x | $0.35M |

Interpretation:

- The selected no-cash GLD strategy was the highest-return tested long-framework variant.
- QQQ remains the clean benchmark. The selected model beat QQQ historically in this framework, but with much more strategy complexity, higher turnover, and larger bias risk.
- BIL was rejected because the GLD defensive sleeve improved the tested return and slightly improved max drawdown.

### Exit-Rule Comparison

The user asked whether the model should sell to avoid downturns. Those variants were tested.

| Strategy | CAGR | Sharpe | Max drawdown | Worst 12m | Turnover |
|---|---:|---:|---:|---:|---:|
| Selected no-cash weekly GLD strategy | 62.61% | 1.77 | -29.70% | -25.40% | 10.11x |
| GLD floors obey 100-day gate | 58.73% | 1.71 | -29.37% | -27.29% | 11.52x |
| GLD all-AI individual 100-day exit | 55.91% | 1.68 | -28.45% | -25.89% | 15.55x |
| GLD individual 100-day plus QQQ 200-day exit | 55.36% | 1.68 | -27.48% | -24.86% | 17.84x |

Interpretation:

- The hard sell-rule variants reduced some drawdown but lowered CAGR.
- For the user's stated objective, return over conservativeness, the selected no-cash weekly GLD strategy remains the model choice.
- If the user's preference changes toward drawdown control, the best alternative is the GLD individual/QQQ exit family or the floors-obey-100-day-gate variant.

### Cash Reserve Comparison

The user asked whether to keep 10-20% cash to buy dips. Those variants were tested, then the user selected no cash.

| Strategy | CAGR | Sharpe | Max drawdown | Worst 12m | Current cash | Current GLD | Current equity |
|---|---:|---:|---:|---:|---:|---:|---:|
| No cash reserve, GLD | 62.61% | 1.77 | -29.70% | -25.40% | 0.00% | 4.75% | 95.25% |
| Dynamic 10% dip reserve | 56.87% | 1.78 | -27.88% | -23.01% | 3.33% | 4.75% | 91.92% |
| Static 10% cash | 55.34% | 1.77 | -26.15% | -23.24% | 10.00% | 4.75% | 85.25% |
| Static 15% cash | 51.76% | 1.77 | -24.68% | -22.18% | 15.00% | 4.75% | 80.25% |
| Static 20% cash | 48.21% | 1.77 | -23.19% | -21.13% | 20.00% | 4.75% | 75.25% |

Interpretation:

- Cash reserves improved drawdown behavior and dip-buy capacity.
- Cash reserves reduced long-run CAGR materially.
- Since the user chose the model's return-maximizing answer, the final strategy uses 0% cash.

### Timing And Return-Mode Grid

The expanded transform grid tested close-to-close, overnight, and intraday return decomposition. These rows are from the base selected transform before the later NBIS/SMCI/GLD overlays.

| Strategy mode | CAGR | Sharpe | Max drawdown | Worst 12m | Turnover |
|---|---:|---:|---:|---:|---:|
| Weekly close-to-close | 55.37% | 1.66 | -31.40% | -24.26% | 10.51x |
| Weekly overnight only | 45.52% | 2.15 | -20.19% | -16.70% | 10.51x |
| Weekly intraday only | 5.54% | 0.35 | -38.97% | -38.55% | 10.51x |
| Monthly close-to-close | 53.77% | 1.60 | -29.71% | -22.60% | 5.24x |
| Monthly overnight only | 46.26% | 2.11 | -18.90% | -16.30% | 5.24x |
| Monthly intraday only | 4.52% | 0.31 | -40.47% | -39.23% | 5.24x |

Interpretation:

- Close-to-close produced the highest total return.
- Overnight had cleaner Sharpe, but an overnight-only strategy is a different trading system with more execution assumptions.
- Intraday-only was weak.
- Weekly close-to-close remained the practical selection.

### No-Rebalance Comparison

Static buy-once/no-rebalance was tested only on the short common window where all current target names/proxies exist.

| Strategy | Window | CAGR | Sharpe | Max drawdown | End value |
|---|---|---:|---:|---:|---:|
| Static buy once, no rebalance | 2025-02-13 to 2026-07-01 | 377.36% | 2.80 | -37.30% | $2.38M |
| Current weekly GLD strategy | 2025-02-13 to 2026-07-01 | 166.12% | 2.46 | -23.97% | $1.07M |

Interpretation:

- Static no-rebalance looked explosive on the short window, but it is not a 10-year proof.
- It also had a deeper drawdown.
- It was not selected as the final strategy because the evidence window is too short and too dependent on recent winners.

## Why This Is The Final Model Choice

The selected model wins because:

1. It had the highest long-framework CAGR among the practical tested variants.
2. It beat the same strategy with BIL.
3. It beat the cash-reserve overlays on CAGR.
4. It kept the user's stated conviction constraints: high NBIS, DRAM instead of SNDK, keep SMCI.
5. It kept QQQ as a 25% core instead of going fully single-theme.
6. It has explicit buy/sell math instead of vague "buy the dip" discretion.

The model was not chosen because it is safe. It was chosen because the user explicitly prefers return over conservativeness.

## Limitations

These are material:

- Current fundamentals are not point-in-time, so the weighting grid has lookahead bias.
- The universe is selected from today's AI/semis winners, so survivorship/theme-selection bias is present.
- NBIS, GEV, SNDK, and DRAM do not provide clean full 10-year live histories.
- DRAM is a live implementation substitute, not a clean historical backtest instrument.
- Taxes are not modeled in the final CAGR tables.
- The strategy turns over about 10x per year, which can create taxable events and slippage.
- A second-source Stooq CSV check failed from this environment with HTTP 404; the full grid remains Yahoo/yfinance-sourced.
- No backtest can validate today's future returns.

## Repo Artifacts

Primary final files:

- `outputs/FINAL_NO_CASH_GLD_STRATEGY.md`
- `outputs/current_1204_exact_order_sheet_GLD_defensive.csv`
- `outputs/exit_rule_comparison_full_results.csv`
- `outputs/cash_dip_reserve_results.csv`
- `outputs/tomorrow_down_10_no_reserve_gld_actions.csv`

Supporting research:

- `outputs/EXIT_RULE_COMPARISON.md`
- `outputs/CASH_DIP_RESERVE_BACKTEST.md`
- `outputs/NBIS_STORAGE_TILT.md`
- `outputs/SMCI_KEEP_BACKTEST.md`
- `outputs/MEDIUM_TRANSFORM_GRID_SEARCH.md`
- `outputs/TRANSFORM_GRID_UPDATE.md`

Key scripts:

- `work/medium_transform_grid.py`
- `work/nbis_storage_tilt_grid.py`
- `work/smci_keep_backtest.py`
- `work/exit_rule_comparison.py`
- `work/cash_dip_reserve_backtest.py`
