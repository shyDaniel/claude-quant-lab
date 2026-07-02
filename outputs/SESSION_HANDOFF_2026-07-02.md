# Session Handoff — July 1-2, 2026

Source: Claude handoff pasted to Codex on 2026-07-02. This file records the operational state and decisions that were not yet in the repo.

## 1. Execution State

Original 12:04 order sheet was not executed. Later on July 1:

- `SMCI`: sold all 300 shares, roughly `$8,352`; loss harvested. No re-buy before `2026-08-02` because of wash-sale window.
- `MU`: bought `+33` shares, moving from `27` to `60` shares. This is the conviction boost and is considered done.
- Not executed: `GEV`, `VRT`, `GLD`.
- Cash remaining: `$59,754.09`.
- Holdings at July 1 19:14 HST: `QQQ 95`, `MU 60`, `NBIS 199`, `DRAM 308.01`, `NVDA 100.01`.

Context: July 1 was a violent AI selloff. Sleeve roughly `-7.9%`; `NBIS -17%`, `MU -10.6%`, `SNDK -10.6%`.

## 2. Final Target Portfolio v3

User constraints: no new `NVDA`, no `SNDK`, no `AMD`; `SMCI` is out.

| Ticker | Target | Status |
|---|---:|---|
| QQQ | ~24.7% | Hold, no trades |
| MU | 22.1% | Done |
| NBIS | ~16.6% | Hold as-is |
| GEV | 10.0% | Buy via tranches |
| NVDA | ~7.1% | Hold, no adds |
| DRAM | ~7.3% | Hold |
| VRT | 5.0% | Buy via tranches |
| GLD | residual ~6.5-7.2% | Buy via tranches |
| SMCI/SNDK/AMD | 0% | Do not buy |

Memory complex is approximately `29.4%` plus `DRAM` look-through, under the 30% tested cap. Physical-bottleneck sleeve `GEV + VRT = 15%`.

## 3. Deployment Method

Lump-sum-before-weekend is canceled. Replacement:

- Three scheduled tranches of about `$20k`: `2026-07-06`, `2026-07-09`, `2026-07-14`.
- Morning executions only.
- Never at night.
- Never off-schedule unless the accelerator is explicitly adopted.
- Each tranche buys the most-underweight allowed targets.
- Default near-target split: `GEV $9.2k / GLD $6.2k / VRT $4.6k`.
- No sells for rebalancing.
- Future contributions buy underweights.

Accelerator status: offered, not adopted. If `MU` closes Thursday `2026-07-02` at or below `-10%`, tranche 1 may execute near Thursday close into most-underweight. Default is no accelerator and tranche 1 remains Monday.

## 4. Standing Rules

- Exit gate: equity sleeve excluding `GLD` vs trailing 252-trading-day high, checked at month-end close only.
- If sleeve closes more than 15% below that high, move stock basket to `GLD`.
- Re-enter when sleeve is back within 15% of rolling high.
- Next check: `2026-07-31`.
- At July 1 close, sleeve was `-12.3%` from high, about `3.1%` above trigger.

Tripwires:

- DRAM/NAND contract-price rollover.
- MU September guide deceleration.
- Further HBM stack-count cuts.
- Enterprise token budget wall in hyperscaler/neocloud guidance.
- Verified NBIS kill-news, such as Meta contract loss or financing failure, is a same-day sell exception.
- Around `2026-08-15`: review Aschenbrenner Q2 13F chip put book.
- User-set max drawdown line, suggested `-45%`, should trigger shift to 70/30 QQQ blend, never cash.

Behavioral protocol:

- Daylight-only decisions.
- Hard-stop rule.
- Trading app logged out and notifications off.
- Monthly 10-minute review plus month-end gate check plus annual review.
- Optional Monday hearing for deliberate MU tilt up to 35% memory line, daylight only.

Tax ops:

- Keep lot log outside the trading app.
- July 1-2 lots turn long-term on `2027-07-03`.
- Approximate short-term marginal rate: 50%.
- `GLD` may be taxed at collectibles rate.
- Reserve about 50% of realized gains quarterly.
- `2026-09-15` estimate should include YTD gains net of SMCI loss.

## 5. Watchlist

- `VST`: buy 2-3% if it reclaims 100dma.
- `AVGO`: gate reclaim.
- `INTC`: contribution touch if margins are actually positive.
- `BABA`: 100dma reclaim plus Pentagon 1260H legal clarity; <=2% if overridden earlier.
- `OKLO`: NRC combined license for Aurora or first revenue; DOE test-reactor approvals do not count.
- `SMCI`: eligible after `2026-08-02`; underwrite only on Nov trial resolution/DOJ corporate declination, two quarters gross-margin stabilization, or 100dma reclaim.
- `MRVL`: in-system photonics route.
- Robots/pre-revenue: new-savings lottery rule, <=2-3%.

## 6. Research Claims To Reproduce

- GEV correction: 2026 peak was June 30 at `$1,174.86`; the stale `-25% off April highs` claim is retracted.
- GEV 60-day return correlations: `MU 0.48`, `NVDA 0.35`, `NBIS 0.32`, `QQQ 0.55`.
- Forward P/E board: `MU 6.9`, `SMCI 8.7`, `SNDK 10.9`, `VST 14.2`, `NVDA 15.5`, `CEG 17.4`, `AVGO 19.0`, `STX 33.6`, `VRT 35.2`, `ANET 37.4`, `AMD 41.0`, `MRVL 44.0`, `GEV 46.2`, `INTC 81.7`, `NBIS 634`.
- MU big-drop event study, 2004-2026: 68 days <= `-8%`; all events median 12-month forward `+94.3%`; above-200dma current-regime median 12-month `+15.1%`, median 6-month `+34.8%`, n=14.
- Dip-deployment replay: staging has about the same EV as all-in but smaller tail; adopted for tranche deployment.

## 7. Implementation Checklist

- Add this handoff file.
- Add v3 spec and tranche deployment tool.
- Add event-study/replay scripts or mark their reproduction as open.
- Update old strategy docs to point to v3.
- Refresh price/fundamental caches before July 6 tranche.
- Calendar: July 2 accelerator check; July 6/9/14 tranches; July 31 gate; August 2 SMCI wash opens; around August 15 13F; September 15 estimated tax; MU September guide.

All numbers remain research, not financial or tax advice. Bias caveats remain: survivorship, lookahead, small event samples, proxy replays, and Yahoo-only data.
