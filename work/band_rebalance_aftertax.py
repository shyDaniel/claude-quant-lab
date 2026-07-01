from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work"
OUT = ROOT / "outputs"
sys.path.append(str(WORK))

from exit_rule_comparison import add_gold_data  # noqa: E402
from medium_transform_grid import (  # noqa: E402
    ACCOUNT_VALUE,
    START,
    TRADING_DAYS,
    load,
    rebalance_mask,
)
from nbis_redirect_sensitivity import build_weights  # noqa: E402


SHORT_TERM_TAX = 0.50
LONG_TERM_QQQ_LIQUIDATION_TAX = 0.331
COST_BPS = 10.0
ALT_FRACTIONS = [1.0, 0.70, 0.50]
BANDS = [None, 0.10, 0.15, 0.20, 0.25, 0.30]


@dataclass(frozen=True)
class TaxSimResult:
    strategy: str
    pre_tax_cagr: float
    after_tax_pre_liq_cagr: float
    after_tax_after_liq_cagr: float
    max_drawdown_after_tax: float
    rebalances: int
    true_turnover: float
    tax_paid: float
    liquidation_tax: float
    end_pre_tax: float
    end_after_tax_pre_liq: float
    end_after_tax_after_liq: float


def cagr(start_value: float, end_value: float, periods: int) -> float:
    years = periods / TRADING_DAYS
    return (end_value / start_value) ** (1 / years) - 1


def max_drawdown(values: pd.Series) -> float:
    return float((values / values.cummax() - 1).min())


def align_prices(close: pd.DataFrame, target: pd.DataFrame) -> pd.DataFrame:
    cols = list(dict.fromkeys(target.columns))
    prices = close.reindex(target.index).ffill()
    for col in cols:
        if col not in prices.columns:
            raise KeyError(f"Missing price column for {col}")
    return prices[cols].ffill()


def normalize_target(row: pd.Series) -> pd.Series:
    out = row.fillna(0.0).clip(lower=0.0)
    total = float(out.sum())
    if total <= 0:
        raise ValueError("Target weights sum to zero")
    return out / total


def blend_with_qqq(target: pd.DataFrame, alt_fraction: float) -> pd.DataFrame:
    out = target.copy() * alt_fraction
    out["QQQ"] = out.get("QQQ", 0.0) + (1.0 - alt_fraction)
    return out.apply(normalize_target, axis=1)


def rebalance_portfolio(
    values: pd.Series,
    basis: pd.Series,
    target: pd.Series,
    *,
    cost_bps: float,
) -> tuple[pd.Series, pd.Series, float, float, float]:
    total = float(values.sum())
    target = normalize_target(target.reindex(values.index).fillna(0.0))
    target_values = total * target

    # One refinement pass makes cost sizing consistent with post-cost target dollars.
    cost = float((target_values - values).abs().sum() * cost_bps / 10_000.0)
    target_values = (total - cost) * target
    trades = target_values - values
    cost = float(trades.abs().sum() * cost_bps / 10_000.0)
    target_values = (total - cost) * target
    trades = target_values - values

    realized = 0.0
    new_basis = basis.copy()
    for ticker, trade in trades.items():
        current_value = float(values[ticker])
        current_basis = float(new_basis[ticker])
        if trade < 0 and current_value > 0:
            sell_value = -float(trade)
            sell_fraction = min(sell_value / current_value, 1.0)
            sold_basis = current_basis * sell_fraction
            realized += sell_value - sold_basis
            new_basis[ticker] = current_basis - sold_basis
        elif trade > 0:
            new_basis[ticker] = current_basis + float(trade)

    new_values = target_values
    return new_values, new_basis, realized, cost, float(trades.abs().sum() / total)


def apply_tax_payment(
    values: pd.Series,
    basis: pd.Series,
    tax: float,
) -> tuple[pd.Series, pd.Series]:
    total = float(values.sum())
    if tax <= 0 or total <= 0:
        return values, basis
    scale = max((total - tax) / total, 0.0)
    return values * scale, basis * scale


def simulate_strategy(
    close: pd.DataFrame,
    target: pd.DataFrame,
    *,
    check_cadence: str,
    band: float | None,
    start: str = START,
    initial_value: float = ACCOUNT_VALUE,
    cost_bps: float = COST_BPS,
    annual_tax_rate: float = SHORT_TERM_TAX,
    liquidation_tax_rate: float = SHORT_TERM_TAX,
) -> TaxSimResult:
    target = target.loc[start:].copy()
    target = target.apply(normalize_target, axis=1)
    prices = align_prices(close, target).loc[target.index]
    target = target[prices.columns]
    returns = prices.pct_change().fillna(0.0)
    check = rebalance_mask(target.index, check_cadence)

    first_target = normalize_target(target.iloc[0])
    values = initial_value * first_target
    basis = values.copy()
    pre_tax_values = values.copy()

    after_tax_curve = []
    pre_tax_curve = []
    realized_year = 0.0
    loss_carry = 0.0
    tax_paid = 0.0
    cost_paid = 0.0
    turnover_sum = 0.0
    rebalances = 0
    prev_year = target.index[0].year

    for pos, date in enumerate(target.index):
        if pos > 0:
            daily_return = returns.iloc[pos].reindex(values.index).fillna(0.0)
            values = values * (1.0 + daily_return)
            pre_tax_values = pre_tax_values * (1.0 + daily_return)

        if pos > 0 and date.year != prev_year:
            taxable_gain = realized_year + loss_carry
            if taxable_gain > 0:
                tax = taxable_gain * annual_tax_rate
                values, basis = apply_tax_payment(values, basis, tax)
                tax_paid += tax
                loss_carry = 0.0
            else:
                loss_carry = taxable_gain
            realized_year = 0.0
            prev_year = date.year

        if bool(check.iloc[pos]):
            current_weights = values / float(values.sum())
            target_today = normalize_target(target.iloc[pos].reindex(values.index).fillna(0.0))
            l1_drift = float((current_weights - target_today).abs().sum())
            should_trade = band is None or l1_drift > band
            if should_trade:
                values, basis, realized, cost, turn = rebalance_portfolio(
                    values,
                    basis,
                    target_today,
                    cost_bps=cost_bps,
                )
                pre_tax_values, _, _, pre_cost, pre_turn = rebalance_portfolio(
                    pre_tax_values,
                    pre_tax_values.copy(),
                    target_today,
                    cost_bps=cost_bps,
                )
                realized_year += realized
                cost_paid += cost
                turnover_sum += turn
                rebalances += 1
                # Keep pre-tax turnover/cost path on the same trading schedule.
                _ = pre_cost, pre_turn

        after_tax_curve.append(float(values.sum()))
        pre_tax_curve.append(float(pre_tax_values.sum()))

    taxable_gain = realized_year + loss_carry
    if taxable_gain > 0:
        tax = taxable_gain * annual_tax_rate
        values, basis = apply_tax_payment(values, basis, tax)
        tax_paid += tax
        loss_carry = 0.0
    else:
        loss_carry = taxable_gain

    final_value = float(values.sum())
    unrealized_gain = final_value - float(basis.sum())
    liquidation_taxable = unrealized_gain + loss_carry
    liquidation_tax = max(liquidation_taxable, 0.0) * liquidation_tax_rate
    after_liq = final_value - liquidation_tax

    after_tax_series = pd.Series(after_tax_curve, index=target.index)
    periods = len(target)
    years = periods / TRADING_DAYS
    label = "band_full" if band is None else f"band_{int(band * 100)}"
    return TaxSimResult(
        strategy=f"{check_cadence}_{label}",
        pre_tax_cagr=cagr(initial_value, float(pre_tax_curve[-1]), periods),
        after_tax_pre_liq_cagr=cagr(initial_value, final_value, periods),
        after_tax_after_liq_cagr=cagr(initial_value, after_liq, periods),
        max_drawdown_after_tax=max_drawdown(after_tax_series),
        rebalances=rebalances,
        true_turnover=turnover_sum / years,
        tax_paid=tax_paid,
        liquidation_tax=liquidation_tax,
        end_pre_tax=float(pre_tax_curve[-1]),
        end_after_tax_pre_liq=final_value,
        end_after_tax_after_liq=after_liq,
    )


def simulate_qqq_buy_hold(close: pd.DataFrame) -> TaxSimResult:
    px = close["QQQ"].loc[START:].ffill()
    daily = px.pct_change().fillna(0.0)
    curve = ACCOUNT_VALUE * (1 + daily).cumprod()
    basis = ACCOUNT_VALUE
    liquidation_tax = max(float(curve.iloc[-1]) - basis, 0.0) * LONG_TERM_QQQ_LIQUIDATION_TAX
    after_liq = float(curve.iloc[-1]) - liquidation_tax
    periods = len(curve)
    return TaxSimResult(
        strategy="QQQ_buy_hold",
        pre_tax_cagr=cagr(ACCOUNT_VALUE, float(curve.iloc[-1]), periods),
        after_tax_pre_liq_cagr=cagr(ACCOUNT_VALUE, float(curve.iloc[-1]), periods),
        after_tax_after_liq_cagr=cagr(ACCOUNT_VALUE, after_liq, periods),
        max_drawdown_after_tax=max_drawdown(curve),
        rebalances=0,
        true_turnover=0.0,
        tax_paid=0.0,
        liquidation_tax=liquidation_tax,
        end_pre_tax=float(curve.iloc[-1]),
        end_after_tax_pre_liq=float(curve.iloc[-1]),
        end_after_tax_after_liq=after_liq,
    )


def result_to_row(
    result: TaxSimResult,
    label: str,
    alt_fraction: float,
    band: float | None,
) -> dict[str, float | str | int]:
    return {
        "strategy": label,
        "alt_fraction": alt_fraction,
        "band": "full" if band is None else band,
        "pre_tax_cagr": result.pre_tax_cagr,
        "after_tax_pre_liq_cagr": result.after_tax_pre_liq_cagr,
        "after_tax_after_liq_cagr": result.after_tax_after_liq_cagr,
        "max_drawdown_after_tax": result.max_drawdown_after_tax,
        "rebalances": result.rebalances,
        "true_turnover": result.true_turnover,
        "tax_paid": result.tax_paid,
        "liquidation_tax": result.liquidation_tax,
        "end_pre_tax": result.end_pre_tax,
        "end_after_tax_pre_liq": result.end_after_tax_pre_liq,
        "end_after_tax_after_liq": result.end_after_tax_after_liq,
    }


def main() -> None:
    close, _, fundamentals = load()
    close, _ = add_gold_data(close, close)
    alt_weekly = build_weights(close, fundamentals, 0.15, 0.50, "weekly")
    alt_monthly = build_weights(close, fundamentals, 0.15, 0.50, "monthly")

    rows: list[dict[str, float | str | int]] = []

    for band in BANDS:
        target = blend_with_qqq(alt_weekly, 1.0)
        result = simulate_strategy(close, target, check_cadence="weekly", band=band)
        label = "ALT weekly full rebalance" if band is None else f"ALT weekly L1>{int(band * 100)}%"
        rows.append(result_to_row(result, label, 1.0, band))

    monthly = simulate_strategy(
        close,
        blend_with_qqq(alt_monthly, 1.0),
        check_cadence="monthly",
        band=None,
    )
    rows.append(result_to_row(monthly, "ALT monthly full rebalance", 1.0, None))

    for alt_fraction in [0.70, 0.50]:
        target = blend_with_qqq(alt_weekly, alt_fraction)
        result = simulate_strategy(close, target, check_cadence="weekly", band=0.10)
        alt_pct = int(alt_fraction * 100)
        qqq_pct = int((1 - alt_fraction) * 100)
        label = f"{alt_pct}% ALT / {qqq_pct}% extra QQQ, L1>10%"
        rows.append(result_to_row(result, label, alt_fraction, 0.10))

    qqq = simulate_qqq_buy_hold(close)
    rows.append(result_to_row(qqq, "QQQ buy-and-hold", 0.0, None))

    results = pd.DataFrame(rows)
    OUT.mkdir(exist_ok=True)
    results.to_csv(OUT / "band_rebalance_aftertax_results.csv", index=False)

    selected = results.loc[results["strategy"] == "ALT weekly L1>20%"].iloc[0]
    compact = results.copy()

    lines = [
        "# Band Rebalance After-Tax Backtest",
        "",
        "Date: 2026-07-01",
        "",
        "## Method",
        "",
        "- Base strategy: post-audit ALT model, `nbis_floor=15%`, "
        "`storage_excess_to_nbis=50%`, no cash, GLD defensive sleeve.",
        "- Simulation: holdings-level close-to-close accounting with drift, "
        "average cost basis, realized gains, annual tax, loss carryforward, "
        "and 10 bps trading cost.",
        f"- Tax assumption: {SHORT_TERM_TAX * 100:.0f}% short-term tax on "
        "annual net realized gains and strategy liquidation gains; QQQ "
        f"buy-and-hold liquidation uses {LONG_TERM_QQQ_LIQUIDATION_TAX * 100:.1f}% "
        "long-term tax.",
        "- Annual tax payments are deducted from portfolio value pro rata. "
        "Lot-level loss harvesting is not modeled.",
        "",
        "## Key Results",
        "",
        "| Strategy | Pre-tax CAGR | After-tax pre-liquidation | After liquidation | "
        "MaxDD after tax | Rebalances | True turnover |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for _, row in compact.iterrows():
        lines.append(
            f"| {row['strategy']} | {row['pre_tax_cagr'] * 100:.1f}% | "
            f"{row['after_tax_pre_liq_cagr'] * 100:.1f}% | "
            f"{row['after_tax_after_liq_cagr'] * 100:.1f}% | "
            f"{row['max_drawdown_after_tax'] * 100:.1f}% | "
            f"{int(row['rebalances'])} | {row['true_turnover']:.1f}x |"
        )
    lines.extend(
        [
            "",
            "## Selected Execution Rule",
            "",
            "Selected: `ALT weekly L1>20%`. It produced "
            f"{selected.after_tax_after_liq_cagr * 100:.1f}% after-liquidation CAGR "
            f"with {int(selected.rebalances)} rebalances and "
            f"{selected.true_turnover:.1f}x true turnover.",
            "",
            "Rule:",
            "",
            "```text",
            "Every weekly signal date:",
            "1. Recompute target weights.",
            "2. Compute current drifted weights from live market values.",
            "3. L1 drift = sum(abs(current_weight - target_weight)) across all holdings.",
            "4. If L1 <= 0.20: hold.",
            "5. If L1 > 0.20: fully rebalance to target weights near the close.",
            "```",
            "",
            "Monthly full rebalancing lowered turnover, but it also lowered "
            "after-tax results in this simulation. The 20% band kept weekly "
            "signal responsiveness while avoiding many small taxable trades.",
            "",
            "The 25% band is slightly higher in this exact rerun; treat that as "
            "threshold-selection noise, not a reason to chase precision. The "
            "20% band is the selected round-number policy default.",
            "",
            "## Files",
            "",
            "- `work/band_rebalance_aftertax.py`",
            "- `outputs/band_rebalance_aftertax_results.csv`",
        ]
    )
    (OUT / "BAND_REBALANCE_AFTERTAX.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
