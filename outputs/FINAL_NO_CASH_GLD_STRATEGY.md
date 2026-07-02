# Final No-Cash GLD Strategy

> Superseded for the taxable account by `outputs/FINAL_TAXABLE_BUY_HOLD_SPEC_V3.md`.
> Keep this file as the record of the earlier band-rebalanced model. The current live-account default is no scheduled sell-to-rebalance, three daylight cash tranches, and the month-end catastrophe gate only.

Date: 2026-07-01

## Supersession Note

This band-rebalanced strategy is no longer the latest taxable-account default. After the buy-and-hold after-tax comparison and catastrophe-gate sweep, the latest taxable return-max spec is:

- `outputs/FINAL_TAXABLE_BUY_HOLD_SPEC_V2.md`

Keep this document as the full record of the ALT weekly L1-band strategy, but use v2 for the current taxable-account recommendation.

## Decision

The selected execution model is the **no-cash-reserve, weekly-signal, band-rebalanced, GLD-defensive AI/semis strategy**.

## Post-Claude Audit Response

Claude's independent audit found no fabrication in the checkable math, but it correctly identified two important implementation gaps and one strategy-design issue:

- GLD was not cached, so offline reproduction of GLD rows failed.
- The 12:04 order-sheet generator was not committed.
- Today's 26.4537% NBIS target came mostly from `storage_excess_to_nbis=1.00`, not from the explicit 25% floor.

The repo now fixes the first two gaps with `work/cache/gld_prices.csv` and `work/current_1204_order_sheet.py`.

The strict max-CAGR model is still the pre-tax argmax. However, after the audit, the cleaner real-money no-cash variant is:

```text
nbis_floor = 15%
storage_excess_to_nbis = 50%
signal check = weekly
trade rule = full rebalance only when L1 drift > 20%
cash = 0%
GLD defensive sleeve unchanged
```

That version reduces current NBIS from 26.45% to 20.73% while reducing cached-GLD CAGR from 62.61% to 60.93%. That 1.68 percentage-point backtest give-up is small relative to the model's survivorship, lookahead, short-history, and tax uncertainty. Use the original 26.45% NBIS version only if intentionally choosing maximum NBIS concentration.

Plain English:

- Do not keep a cash sleeve.
- Keep QQQ as a 25% core.
- Put the rest into a concentrated AI/semis basket, with NBIS capped down from the earlier 26.45% version by using a lower storage-overflow redirect.
- Use GLD as the defensive/overflow sleeve instead of BIL or cash.
- Keep SMCI at the current small position size.
- Use DRAM as the live memory/HBM bucket instead of buying SNDK.
- Check signals weekly, but trade only when the portfolio is more than 20% L1 away from target.

This is no longer the strict pre-tax max-CAGR row. It is the tax-aware execution choice: accept a small pre-tax give-up versus the 26.45% NBIS version, then reduce taxable churn by trading only when drift is large. The tradeoff is that it still gives up the psychological comfort of dry powder. If the portfolio drops sharply tomorrow, the model can only buy the dip by trimming GLD or overweight names.

This is rule-based research, not fiduciary advice or a guarantee.

## Current Target Weights

These are the post-audit ALT target weights: no cash, no BIL, GLD defensive sleeve, DRAM instead of SNDK, keep SMCI, NBIS floor 15%, storage excess redirect 50%.

| Ticker | Target weight | Role |
|---|---:|---|
| QQQ | 25.0000% | Core Nasdaq-100 growth exposure |
| NBIS | 20.7268% | AI infrastructure plus reduced storage-overflow redirect |
| MU | 19.8080% | Memory/HBM cycle exposure |
| NVDA | 10.9896% | AI accelerator/platform exposure |
| DRAM | 7.4159% | Live substitute for historical SNDK memory slot |
| GLD | 4.7451% | Gold defensive/overflow sleeve |
| GEV | 4.3550% | AI power/electrification exposure |
| AMD | 3.9286% | AI/compute exposure |
| SMCI | 3.0309% | Keep-current-position server exposure |
| Cash | 0.0000% | No reserve |
| BIL | 0.0000% | Rejected defensive asset |
| SNDK | 0.0000% live | Historical proxy only; replaced by DRAM live |
| STX | 0.0000% | Removed to make room for SMCI |

Target weights sum to 100%.

## Current Order Sheet

Based on the user's 12:04 screenshot and total account value of $278,726.16. Use target weights if live quotes or buying power differ.

| Action | Ticker | Target value | Current value | Trade dollars | Approx shares |
|---|---:|---:|---:|---:|---:|
| Buy | NBIS | $57,771.14 | $46,168.91 | $11,602.23 | 50.01 |
| Buy | MU | $55,210.08 | $27,999.61 | $27,210.47 | 26.24 |
| Buy | GLD | $13,225.95 | $0.00 | $13,225.95 | 35.69 |
| Buy | GEV | $12,138.56 | $0.00 | $12,138.56 | 10.70 |
| Buy | AMD | $10,950.00 | $0.00 | $10,950.00 | 20.24 |
| Buy | NVDA | $30,630.76 | $19,759.61 | $10,871.15 | 55.02 |
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

On each weekly signal date:

```text
1. Compute raw_score for every AI/semis name.
2. Keep the top 7 positive-scoring names.
3. Normalize their scores to sum to the 70% AI/semis sleeve.
4. Add the fixed 25% QQQ core.
5. Route unallocated/defensive weight to GLD.
```

### NBIS Overlay

The post-audit ALT model handles NBIS with both a floor and a storage-overflow redirect:

```text
NBIS floor = 15% of account
NBIS activation policy = tradable_with_history
storage cap = 30% of account across MU/SNDK/STX in the historical model
storage excess redirect = 50% to NBIS when NBIS is active
```

This means NBIS does not need to be above its 100-day moving average to receive the overlay. It needs to have enough valid trading history. That is an intentional conviction/redirect override, not something the pure optimizer discovered from 10 years of NBIS data.

Important correction from independent audit: today's 26.4537% NBIS target is **not mainly the 25% floor**. On 2026-07-01:

```text
base model NBIS score weight = 2.6219%
base model storage weight before cap = 53.8318%
storage cap = 30.0000%
storage excess redirected to NBIS = 23.8318%
final NBIS weight = 2.6219% + 23.8318% = 26.4537%
```

So the original pre-tax max-CAGR model owned 26.4537% NBIS because `storage_excess_to_nbis=1.00` redirected the memory/storage excess into NBIS. The post-audit ALT model uses `nbis_floor=15%` and `storage_excess_to_nbis=0.50`, cutting today's NBIS target to 20.7268%.

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

### Signal And Band-Rebalance Rule

Compute signals weekly, using the last trading day of the week. Do **not** automatically trade every week. The execution rule is a 20% L1 band:

```text
After or near the weekly close:
1. Calculate the new target weights.
2. Calculate current drifted weights from live position values.
3. L1 drift = sum(abs(current_weight - target_weight)).
4. If L1 <= 0.20: hold.
5. If L1 > 0.20: fully rebalance to target weights.
6. Keep cash at 0% except rounding.
```

Close-to-close means:

```text
daily_return = adjusted_close_today / adjusted_close_yesterday - 1
```

It is the return measurement mode in the backtest. It does not mean the model recomputes and rebalances every day.

### When To Buy

Buy only when the L1 band triggers and:

```text
target_dollars > current_position_value
```

The buy amount is:

```text
buy_dollars = target_dollars - current_position_value
```

Example: if NBIS dips while its model target remains 20.7268%, the strategy buys enough NBIS at the next triggered rebalance to restore NBIS to the target weight, funded by trimming cash, GLD, or overweight positions.

### When To Sell

Sell only when the L1 band triggers and:

```text
target_dollars < current_position_value
```

The sell amount is:

```text
sell_dollars = current_position_value - target_dollars
```

For NBIS specifically, the model sells NBIS in these situations:

1. NBIS rallies enough that it becomes above its target weight, then a triggered rebalance trims it back.
2. The storage/score overlay no longer redirects enough weight to NBIS and the NBIS target falls toward the active floor or base score.
3. NBIS loses valid tradable history or otherwise becomes ineligible in the data; then the conviction floor turns off and the base score determines target weight.
4. The user explicitly switches to the lower-drawdown variant where conviction floors obey the 100-day moving-average gate.

The selected model does **not** sell NBIS merely because it falls below the 100-day moving average. That hard-exit version was tested and rejected for the user's chosen return-maximizing objective.

### Current 12:04 Band Decision

The default live band tool sees the 12:04 screenshot as a trade because cash is still unallocated:

```text
L1 drift: 0.6252
Band: 0.2000
Decision: TRADE
```

After the initial deployment, the same rule should usually hold through small weekly drift and only trade when the portfolio gets meaningfully far from target.

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
- GLD is now cached in `work/cache/gld_prices.csv` so offline reruns do not depend on a live Yahoo request.

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
| Taxes | Modeled only in the after-tax band section; other CAGR tables are pre-tax |
| Margin | None |
| Options | None |
| Dividends | Adjusted-price data where available |
| Rebalance execution | Weekly signal; full rebalance only if L1 drift > 20% |
| Daily return mode | Close-to-close unless otherwise stated |

## Backtest Results

### Main Long Framework Window

Window: `2016-07-01` to `2026-07-01`. Starting account value for end-value math: `$278,726.16`.

| Strategy | CAGR | Sharpe | Max drawdown | Worst 12m | Target-diff turnover | End value |
|---|---:|---:|---:|---:|---:|---:|
| Original pre-tax max-CAGR GLD reference | 62.61% | 1.77 | -29.70% | -25.40% | 10.11x | $35.55M |
| Same strategy with BIL defensive sleeve | 56.60% | 1.66 | -30.85% | -22.09% | 10.11x | $24.41M |
| QQQ buy-and-hold | 21.94% | 1.00 | -35.12% | -34.76% | 0.00x | $2.01M |
| BIL buy-and-hold | 2.19% | 8.01 | -0.26% | -0.13% | 0.00x | $0.35M |

Interpretation:

- The original no-cash GLD reference was the highest pre-tax long-framework variant.
- QQQ remains the clean benchmark. The selected model beat QQQ historically in this framework, but with much more strategy complexity, higher turnover, and larger bias risk.
- BIL was rejected because the GLD defensive sleeve improved the tested return and slightly improved max drawdown.

### Exit-Rule Comparison

The user asked whether the model should sell to avoid downturns. Those variants were tested.

| Strategy | CAGR | Sharpe | Max drawdown | Worst 12m | Turnover |
|---|---:|---:|---:|---:|---:|
| Original pre-tax max-CAGR GLD reference | 62.61% | 1.77 | -29.70% | -25.40% | 10.11x |
| GLD floors obey 100-day gate | 58.73% | 1.71 | -29.37% | -27.29% | 11.52x |
| GLD all-AI individual 100-day exit | 55.91% | 1.68 | -28.45% | -25.89% | 15.55x |
| GLD individual 100-day plus QQQ 200-day exit | 55.36% | 1.68 | -27.48% | -24.86% | 17.84x |

Interpretation:

- The hard sell-rule variants reduced some drawdown but lowered CAGR.
- For the user's stated objective, return over conservativeness, the no-cash GLD family remains the model choice.
- If the user's preference changes toward drawdown control, the best alternative is the GLD individual/QQQ exit family or the floors-obey-100-day-gate variant.

### NBIS Redirect Sensitivity

Claude's independent audit suggested cutting the NBIS floor and storage redirect. The exact cached-GLD rerun shows:

| Strategy | CAGR | Sharpe | Max drawdown | Worst 12m | Turnover | Current NBIS |
|---|---:|---:|---:|---:|---:|---:|
| Pre-tax reference: floor 25%, redirect 100%, weekly | 62.61% | 1.77 | -29.70% | -25.40% | 10.11x | 26.45% |
| Post-audit ALT: floor 15%, redirect 50%, weekly | 60.93% | 1.76 | -29.70% | -25.40% | 10.20x | 20.73% |
| Post-audit ALT: floor 15%, redirect 50%, monthly | 56.18% | 1.62 | -30.16% | -20.31% | 5.14x | 20.73% |

Interpretation: the lower-redirect weekly version gives up 1.68 percentage points of backtested CAGR while cutting the largest single-name weight from 26.45% to 20.73%. That difference is small relative to the model's known bias and tax uncertainty, so the lower-redirect variant is a defensible risk-control modification.

### After-Tax Band-Rebalance Test

Claude correctly identified the missing decision-relevant test: taxable-account rebalancing. The repo now includes a holdings-level simulator with drifted positions, average cost basis, realized gains, annual tax payment, loss carryforward, 10 bps costs, and liquidation tax.

This simulator is intentionally stricter than the Claude table because annual tax payments are deducted from portfolio value pro rata. The exact numbers are lower than Claude's, but the conclusion is the same: band rebalancing beats forced weekly rebalancing after tax, and monthly is not the tax fix.

Window: `2016-07-01` to `2026-07-01`. Tax assumption: 50% short-term tax on strategy realized gains and liquidation gains; 33.1% long-term liquidation tax for QQQ buy-and-hold.

| Strategy | Pre-tax CAGR | After-tax pre-liquidation | After liquidation | MaxDD after tax | Rebalances | True turnover |
|---|---:|---:|---:|---:|---:|---:|
| ALT weekly full rebalance | 60.3% | 36.8% | 34.5% | -39.3% | 523 | 11.0x |
| ALT weekly L1>10% | 60.4% | 37.7% | 35.0% | -38.5% | 268 | 10.1x |
| ALT weekly L1>15% | 59.5% | 37.6% | 34.9% | -38.8% | 189 | 9.4x |
| **ALT weekly L1>20% selected** | **60.2%** | **38.5%** | **35.5%** | **-38.8%** | **147** | **8.9x** |
| ALT weekly L1>25% | 61.4% | 39.4% | 36.3% | -39.1% | 126 | 8.5x |
| ALT weekly L1>30% | 60.6% | 39.4% | 35.8% | -37.8% | 106 | 8.0x |
| ALT monthly full rebalance | 56.5% | 36.7% | 33.6% | -41.3% | 121 | 5.6x |
| 70% ALT / 30% extra QQQ, L1>10% | 48.1% | 31.8% | 29.1% | -37.3% | 205 | 6.7x |
| 50% ALT / 50% extra QQQ, L1>10% | 40.1% | 28.5% | 25.5% | -37.2% | 160 | 4.6x |
| QQQ buy-and-hold | 21.9% | 21.9% | 17.8% | -35.1% | 0 | 0.0x |

Interpretation:

- Full weekly rebalancing is no longer the best execution rule once tax is modeled.
- Monthly reduces trading count but gives up too much pre-tax return and loses after liquidation.
- A 25% band is slightly higher in this specific rerun, but that is a threshold-selection warning, not a reason to chase a more precise-looking number. The 20% band is the selected policy default because it was independently proposed, round-number robust, and already captures the tax benefit.
- The chosen live rule is therefore: check weekly, trade only when L1 drift exceeds 20%, then rebalance fully to the current target weights.

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

1. The no-cash GLD family had the highest pre-tax CAGR among the practical tested variants.
2. GLD beat BIL as the defensive/overflow sleeve in the tested framework.
3. Cash-reserve overlays improved dry powder and drawdown, but materially reduced CAGR.
4. The post-audit ALT weights cut NBIS from 26.45% to 20.73% for only a small pre-tax give-up.
5. The after-tax simulator shows band rebalancing beats forced weekly rebalancing after liquidation.
6. It kept the user's stated constraints: high NBIS, DRAM instead of SNDK, keep SMCI, 0% cash.
7. It has explicit buy/sell math instead of vague "buy the dip" discretion.

The model was not chosen because it is safe. It was chosen because the user explicitly prefers return over conservativeness, and because the tax-aware execution rule removes unnecessary small trades without adding discretionary judgment.

## Limitations

These are material:

- Current fundamentals are not point-in-time, so the weighting grid has lookahead bias.
- The universe is selected from today's AI/semis winners, so survivorship/theme-selection bias is present.
- NBIS, GEV, SNDK, and DRAM do not provide clean full 10-year live histories.
- DRAM is a live implementation substitute, not a clean historical backtest instrument.
- Taxes are modeled only in the band-rebalance simulator; it still omits lot selection, tax-loss harvesting, estimated-payment timing, and exact personal tax details.
- The selected 20% band strategy still turns over about 8.9x per year in the simulator, which can create taxable events and slippage.
- A second-source Stooq CSV check failed from this environment with HTTP 404; the full grid remains Yahoo/yfinance-sourced.
- No backtest can validate today's future returns.

## Repo Artifacts

Primary final files:

- `outputs/FINAL_NO_CASH_GLD_STRATEGY.md`
- `outputs/current_1204_exact_order_sheet_GLD_defensive.csv`
- `outputs/exit_rule_comparison_full_results.csv`
- `outputs/cash_dip_reserve_results.csv`
- `outputs/tomorrow_down_10_no_reserve_gld_actions.csv`
- `outputs/NBIS_REDIRECT_SENSITIVITY.md`
- `outputs/alternative_nbis_redirect_order_sheet.csv`
- `outputs/BAND_REBALANCE_AFTERTAX.md`
- `outputs/band_rebalance_aftertax_results.csv`
- `outputs/STRATEGY_COMPARISON_CHARTS.md`
- `outputs/strategy_comparison_full_window.png`
- `outputs/strategy_comparison_common_window.png`
- `outputs/strategy_comparison_drawdowns.png`
- `outputs/BUY_HOLD_ENTRY_TIMING.md`
- `outputs/buy_hold_entry_timing_3y_bars.png`
- `outputs/buy_hold_entry_timing_3y_win_rates.png`
- `outputs/buy_hold_entry_timing_current_basket.png`

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
- `work/current_1204_order_sheet.py`
- `work/nbis_redirect_sensitivity.py`
- `work/band_rebalance_aftertax.py`
- `work/live_band_decision.py`
- `work/strategy_comparison_charts.py`
- `work/buy_hold_entry_timing.py`
