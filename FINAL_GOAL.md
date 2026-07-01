# FINAL_GOAL — claude-quant-lab

## Mission (the competitive charter)
An independent systematic-research lab that races the neighboring Codex project
(`../i`). Codex converged on an honest but deflating conclusion: *nothing un-levered
beats buy-and-hold QQQ after tax*. My job is to attack that conclusion from angles Codex
did NOT test, and either (a) find a real, cost-survivable edge that beats QQQ
risk-adjusted (and hunt for a raw-return beat), or (b) prove — faster and more rigorously
than Codex — that the honest ceiling is what it is, and package the single best
executable answer for the user.

Framing (user's words): Anthropic vs OpenAI. Learn briefly what Codex does, then out-build
it. Strategy is out there in the literature and with the right practitioners — the job is
finding *whom* and testing *honestly*.

## Where I can out-run Codex (Codex's blind spots)
1. Codex only tested QQQ **close-to-close**. It ignored the **overnight vs intraday**
   decomposition entirely — a whole dimension of the data.
2. Codex's **AI/tech sleeve was buggy and capped** (the MU $1,154 data bug; NBIS 8-month
   history). The user WANTS AI exposure. A properly-built **cross-sectional momentum**
   basket on a curated Mag-7 / AI universe is under-explored and is the user's real interest.
3. Codex tested single-signal trend rules; it did not build a **multi-factor / multi-asset
   ensemble** (trend + carry + value + defensive) — the diversify-return-sources approach.
4. Codex's options lane is **model-optimistic** (5bps spreads, under-priced IV). I can hold
   a higher honesty bar on costs from day one.

## Non-negotiable principles (the honesty moat = my competitive advantage)
- **Realistic costs ALWAYS.** Every strategy nets out realistic spread/slippage/commission
  AND (for taxable) after-tax. Kill gross-return mirages on contact (e.g., the overnight
  anomaly dies after costs — I will confirm and report, not chase).
- **Out-of-sample or it didn't happen.** Walk-forward / purged splits; report failures.
- **Executable by THIS user.** A $300k retail investor, taxable-aware, panic-prone, wants
  simplicity. No intraday-HFT fantasies unless truly retail-viable.
- **Head-to-head vs Codex's best.** Every candidate reported vs BuyHold_QQQ AND vs Codex's
  core (QQQ_ABS_MOM_12M: ~13.9% CAGR, Sharpe 0.81, -29% DD, $3.18M after-tax).

## Done looks like
- [ ] Lean vectorized, cost-aware backtester (my own — not Codex's code), Python 3.12.
- [ ] Overnight/intraday decomposition of QQQ tested with realistic costs (confirm/deny edge).
- [ ] Cross-sectional momentum on a curated AI/tech basket, backtested vs QQQ (the user's angle).
- [ ] A multi-factor / multi-asset ensemble tested vs QQQ risk-adjusted.
- [ ] A "QQQ core + un-levered tactical overlay" that tries to ADD, not replace.
- [ ] Each candidate: CAGR, Sharpe, max DD, worst-12mo, after-tax, OOS, turnover, vs QQQ + vs Codex core.
- [ ] A head-to-head scoreboard (`outputs/scoreboard.md`) ranking my strategies AND Codex's core.
- [ ] A final honest verdict: the single best executable strategy for the user, with proof —
      OR a rigorous confirmation of the ceiling, beating Codex to the honest answer.

## Stopping condition
When the scoreboard has a defensible winner (mine or, honestly, Codex's) proven under
realistic costs + OOS, and the user has one clear executable recommendation with proof.
Until then: keep finding sources, keep testing, don't stop at the first "nothing beats QQQ."
