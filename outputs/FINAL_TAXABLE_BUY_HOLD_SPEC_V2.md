# Final Taxable Strategy Spec v2

> Superseded operationally by `outputs/FINAL_TAXABLE_BUY_HOLD_SPEC_V3.md`.
> Keep this file as the evidence record for the taxable buy-and-hold conclusion.

Date: 2026-07-01

## Decision

For this taxable Robinhood account and the user's stated return-max preference, the current best model choice is:

```text
Buy the current target basket once, then hold.
No weekly rebalancing.
No scheduled sell-to-rebalance.
New cash buys the most-underweight target names.
Catastrophe gate is optional insurance, not the max-return taxable default.
```

This supersedes the earlier `ALT weekly L1>20%` band-rebalanced execution as the taxable-account default. The band strategy remains useful as a rules-based discipline model, but its 147 rebalances do not earn their tax bill versus buy-and-hold in the after-tax comparisons.

This is research, not fiduciary or tax advice.

## Current Target Weights

Use the post-audit ALT target basket as the one-time allocation:

| Ticker | Target weight | Role |
|---|---:|---|
| QQQ | 25.0000% | Core Nasdaq-100 growth exposure |
| NBIS | 20.7268% | AI infrastructure plus reduced storage-overflow redirect |
| MU | 19.8080% | Memory/HBM cycle exposure |
| NVDA | 10.9896% | AI accelerator/platform exposure |
| DRAM | 7.4159% | Live substitute for historical SNDK memory slot |
| GLD | 4.7451% | Defensive/overflow sleeve |
| GEV | 4.3550% | AI power/electrification exposure |
| AMD | 3.9286% | AI/compute exposure |
| SMCI | 3.0309% | Keep-current-position server exposure |
| Cash | 0.0000% | No reserve |

If using the 12:04 account snapshot, the order sheet is unchanged from the ALT target sheet:

| Action | Ticker | Trade dollars |
|---|---:|---:|
| Buy | MU | $27,210.47 |
| Buy | GLD | $13,225.95 |
| Buy | GEV | $12,138.56 |
| Buy | NBIS | $11,602.23 |
| Buy | AMD | $10,950.00 |
| Buy | NVDA | $10,871.15 |
| Buy | QQQ | $788.34 |
| Buy | DRAM | $245.77 |
| Buy | SMCI | $93.00 |

Buys total `$87,125.47`, matching the available cash in that snapshot.

## Buy/Sell Rules

### Initial Deployment

Default:

```text
Buy 100% of the target basket now.
```

Regret-control alternative:

```text
Buy 70% now.
Keep 30% temporarily uninvested.
Deploy the 30% if the basket falls 10%, or after 6 months, whichever comes first.
```

The rolling-entry tests favor lump sum on median return. The 70/30 rule is psychological insurance, not a higher-expected-return rule.

### Ongoing

```text
Do not rebalance on a schedule.
Do not trim winners only because weights drift.
Use new deposits to buy the most-underweight target names.
Review thesis quarterly.
Sell only if a prewritten kill criterion is hit, or if choosing the optional catastrophe gate.
```

This is intentionally tax-deferral-first. In taxable, avoiding realized gains is part of the edge.

## Optional Catastrophe Gate

This is insurance, not the taxable max-return default:

```text
At month-end:
1. Treat the stock basket as one index.
2. Compute its trailing 252-trading-day high.
3. If the basket closes more than 15% below that high, sell the basket and hold GLD.
4. While in GLD, re-enter when the basket is back within 15% of its trailing 252-trading-day high.
```

Backtest on equal-weight full-history AI/semis basket:

| Strategy | Pre-tax CAGR | After-liq CAGR | Pre-tax MaxDD | After-tax curve MaxDD | Trades |
|---|---:|---:|---:|---:|---:|
| Buy-hold EW-9 | 50.8% | 45.0% | -54.8% | -54.8% | 0 |
| 15% monthly gate | 53.1% | 37.9% | -28.9% | -36.7% | 12 |
| ALT weekly L1>20% band | 60.2% pre-tax | 35.5% | -29.6% pre-tax | -38.8% | 147 |

Interpretation:

- In taxable: buy-and-hold has the best after-liquidation result.
- In taxable: the 15% gate is drawdown insurance that costs after-tax return.
- In sheltered accounts: the 15% gate is attractive because the pre-tax result dominates and tax deferral is irrelevant.
- The weekly ALT band strategy is still too tax-expensive for taxable max-return use.

## Entry Timing

Rolling entry tests showed lump-sum buy-and-hold is hard to beat:

| Basket | Best median 3y entry rule | Median 3y CAGR | Notes |
|---|---|---:|---|
| QQQ | Lump sum | 20.1% | DCA/waiting usually lost median return |
| Full-history AI/semis | Lump sum | 44.0% | Waiting sometimes beat lump, but not reliably |
| Current target basket single window | DCA/waiting sometimes beat | Not robust | One short survivorship-heavy window |

Current cached extension:

| Basket | Versus 200dma |
|---|---:|
| EW-9 full-history basket | +41.6% |
| Current target basket | +123.8% |

That extension makes 2-3 tranches emotionally reasonable, but the historical median-return rule is still lump sum.

## Why The Answer Changed

The earlier band strategy was selected before the buy-and-hold taxable comparison was fully tested. Once the after-tax deferral comparison was run, the ranking changed:

1. Trading systems can have higher pre-tax CAGRs but lose after tax.
2. Buy-and-hold benefits from tax deferral.
3. The current target basket is highly survivorship-biased, but within that chosen bet, taxable churn is a major enemy.
4. The right taxable implementation is therefore simpler: buy the basket, hold it, and avoid realized gains unless thesis/risk rules force action.

## Files

- `outputs/STRATEGY_COMPARISON_CHARTS.md`
- `outputs/BUY_HOLD_ENTRY_TIMING.md`
- `outputs/CATASTROPHE_GATE_BUY_HOLD.md`
- `work/strategy_comparison_charts.py`
- `work/buy_hold_entry_timing.py`
- `work/catastrophe_gate_buy_hold.py`
