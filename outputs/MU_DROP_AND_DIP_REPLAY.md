# MU Drop Event Study and Dip Deployment Replay

Date: 2026-07-02

Claude handoff claims to reproduce:

- `MU` days <= `-8%`, 2004-2026: `n=68`.
- All such events: median 12-month forward return `+94.3%`.
- Above-200dma current-regime events: median 12-month `+15.1%`, median 6-month `+34.8%`, `n=14`.
- `NBIS` days <= `-10%`: `17` days in `424` sessions.
- Dip deployment replay conclusion: staged `3 x $20k` deployment has approximately the same EV as all-in, with smaller tail risk.

Committed scripts:

- `work/mu_drop_event_study.py`
- `work/dip_deployment_replay.py`

Both scripts write regenerated CSVs to `outputs/`, which are ignored by Git. The replay is proxy-based:

- `NBIS_PROXY = 1.5 x NVDA daily return`, capped at `-85%` daily downside.
- `DRAM_PROXY = 0.75 x MU + 0.25 x STX`.

The scripts should be treated as reproduction harnesses, not a new strategy source. Small sample and proxy caveats are material.

## Codex Smoke Run

Using Yahoo data on 2026-07-02:

| Ticker | Bucket | Events | Median 6m | Median 12m |
|---|---:|---:|---:|---:|
| MU | baseline all dates | 5659 | +8.2% | +11.1% |
| MU | all drop events | 69 | +26.3% | +94.3% |
| MU | above 200dma | 15 | +34.8% | +15.1% |
| MU | below 200dma | 54 | +23.2% | +106.1% |
| NBIS | all drop events | 17 | +133.9% | +251.1% |

Replay smoke output:

| Episode | ALL-IN vs cash | STAGED vs cash | Staged minus all-in |
|---|---:|---:|---:|
| 2018 top | +$6.0k | +$5.9k | -$0.2k |
| 2020 COVID V | +$56.6k | +$77.4k | +$20.8k |
| 2022 top | -$19.0k | -$16.9k | +$2.1k |
| 2025 ignition | +$227.6k | +$224.0k | -$3.5k |

The exact 2025 value differs from Claude's handoff because this committed replay uses a transparent five-trading-day staging proxy and fresh Yahoo history. The decision-relevant conclusion is unchanged: staging is close to all-in on expected value and can improve bad-path regret.
