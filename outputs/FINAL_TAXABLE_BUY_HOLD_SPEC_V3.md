# Final Taxable Strategy Spec v3

Date: 2026-07-02

This supersedes v2 only on live execution state and tranche deployment. The taxable conclusion is unchanged: after tax, the max-return version of this bet is structurally buy-and-hold, not weekly trading.

## Decision

```text
Hold the taxable AI/semis basket.
Deploy the remaining cash in three daylight tranches into the most-underweight allowed targets.
Do not schedule sell-to-rebalance.
Use GLD only as the defensive residual sleeve and catastrophe-gate destination.
```

This is research, not fiduciary or tax advice.

## Current State

Executed after the July 1 drawdown:

- Sold all `SMCI`; do not re-buy before `2026-08-02`.
- Bought `+33` `MU`, bringing `MU` to `60` shares.
- Did not buy `GEV`, `VRT`, or `GLD`.
- Cash remaining: `$59,754.09`.

## v3 Target Weights

| Ticker | Target | Action |
|---|---:|---|
| QQQ | 24.7% | Hold |
| MU | 22.1% | Done, no automatic chase |
| NBIS | 16.6% | Hold |
| GEV | 10.0% | Buy via tranches |
| DRAM | 7.3% | Hold |
| NVDA | 7.1% | Hold, no new adds |
| VRT | 5.0% | Buy via tranches |
| GLD | 7.2% | Buy via tranches; absorbs rounding |
| SMCI/SNDK/AMD | 0.0% | Do not buy |

The committed machine-readable targets are in `config/v3_targets.json`.

## Tranche Rule

Deploy about `$20k` on each scheduled date:

| Date | Action |
|---|---|
| 2026-07-06 | Tranche 1, morning |
| 2026-07-09 | Tranche 2, morning |
| 2026-07-14 | Tranche 3, morning |

For each tranche:

1. Update current position values.
2. Compute target dollars from v3 target weights.
3. Rank positive underweights.
4. Buy only allowed underweights.
5. Allocate the tranche proportional to allowed underweight dollars.
6. Do not sell anything for rebalancing.

Reference split near the handoff snapshot:

```text
GEV  ~$9.2k
GLD  ~$6.2k
VRT  ~$4.6k
```

Use:

```bash
python work/tranche_tool.py --cash-to-deploy 20000
```

With live local holdings:

```bash
python work/tranche_tool.py --holdings config/holdings.local.json --cash-to-deploy 20000
```

## Accelerator

Status: offered, not adopted.

If `MU` closes on `2026-07-02` at or below `-10%`, tranche 1 may execute near that close into most-underweight allowed targets. Unless explicitly adopted, ignore this and keep tranche 1 on `2026-07-06`.

## Sell Rules

No scheduled sells. Sells are allowed only for:

- Month-end catastrophe gate.
- Written kill criterion.
- Tax/legal/compliance necessity.

Catastrophe gate:

```text
At month-end close, compute ex-GLD equity sleeve vs trailing 252-trading-day high.
If more than 15% below that high, move the stock basket to GLD.
Re-enter when the sleeve is back within 15% of the rolling high.
```

Next gate check: `2026-07-31`. As of July 1 close, sleeve was about `-12.3%` from high, roughly `3.1%` above trigger.

## Tripwires

- DRAM/NAND contract-price rollover.
- MU September guide deceleration.
- Further HBM stack-count cuts.
- Enterprise token budget wall in hyperscaler/neocloud guidance.
- NBIS verified kill-news: Meta contract loss or financing failure.
- Around `2026-08-15`: review Aschenbrenner Q2 13F chip put book.
- User-set max drawdown, suggested `-45%`: shift to 70/30 QQQ blend, not cash.

## Why This Version

Claude's latest audit agrees with the v2 taxable conclusion: after tax, trading subtracts unless the user is explicitly buying insurance. Buy-and-hold wins because tax deferral is powerful. The change from v2 is not a new backtest winner; it is a live-account correction after partial execution, a volatile entry day, and user constraints.

The staged deployment is regret control with roughly similar expected value to all-in in the small replay study, not a claim that DCA has higher median return. The point is to finish deployment without panic, at controlled size, in daylight.

## Files

- `outputs/SESSION_HANDOFF_2026-07-02.md`
- `outputs/MU_DROP_AND_DIP_REPLAY.md`
- `config/v3_targets.json`
- `work/tranche_tool.py`
- `work/mu_drop_event_study.py`
- `work/dip_deployment_replay.py`
- `docs/BRIEFING_SERVICE.md`
