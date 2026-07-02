from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work"
OUT = ROOT / "outputs"
sys.path.append(str(WORK))

from band_rebalance_aftertax import (  # noqa: E402
    COST_BPS,
    LONG_TERM_QQQ_LIQUIDATION_TAX,
    SHORT_TERM_TAX,
    apply_tax_payment,
    rebalance_portfolio,
)
from exit_rule_comparison import add_gold_data  # noqa: E402
from medium_transform_grid import ACCOUNT_VALUE, START, TRADING_DAYS, UNIVERSE, load  # noqa: E402
from nbis_redirect_sensitivity import build_weights  # noqa: E402


@dataclass(frozen=True)
class CurveResult:
    label: str
    curve: pd.Series
    rebalances: int = 0
    turnover: float = 0.0
    after_liq_end_value: float | None = None


def normalize(row: pd.Series) -> pd.Series:
    out = row.fillna(0.0).clip(lower=0.0)
    total = float(out.sum())
    if total <= 0:
        raise ValueError("Weights sum to zero")
    return out / total


def weekly_signal_mask(index: pd.DatetimeIndex) -> pd.Series:
    return index.to_series().groupby(
        [index.isocalendar().year, index.isocalendar().week]
    ).transform("max") == index


def simulate_band_curve(
    close: pd.DataFrame,
    target: pd.DataFrame,
    *,
    start: str,
    band: float,
    after_tax: bool,
) -> CurveResult:
    target = target.loc[start:].apply(normalize, axis=1)
    prices = close.reindex(target.index).ffill()[target.columns].ffill()
    target = target[prices.columns]
    returns = prices.pct_change().fillna(0.0)
    check = weekly_signal_mask(target.index)

    values = ACCOUNT_VALUE * normalize(target.iloc[0])
    basis = values.copy()
    curve = []
    realized_year = 0.0
    loss_carry = 0.0
    tax_paid = 0.0
    turnover_sum = 0.0
    rebalances = 0
    prev_year = target.index[0].year

    for pos, date in enumerate(target.index):
        if pos > 0:
            daily_return = returns.iloc[pos].reindex(values.index).fillna(0.0)
            values = values * (1.0 + daily_return)

        if after_tax and pos > 0 and date.year != prev_year:
            taxable_gain = realized_year + loss_carry
            if taxable_gain > 0:
                tax = taxable_gain * SHORT_TERM_TAX
                values, basis = apply_tax_payment(values, basis, tax)
                tax_paid += tax
                loss_carry = 0.0
            else:
                loss_carry = taxable_gain
            realized_year = 0.0
            prev_year = date.year

        if bool(check.iloc[pos]):
            current_weights = values / float(values.sum())
            target_today = normalize(target.iloc[pos].reindex(values.index).fillna(0.0))
            if float((current_weights - target_today).abs().sum()) > band:
                values, basis, realized, _, turnover = rebalance_portfolio(
                    values,
                    basis,
                    target_today,
                    cost_bps=COST_BPS,
                )
                realized_year += realized
                turnover_sum += turnover
                rebalances += 1

        curve.append(float(values.sum()))

    after_liq_end_value = None
    if after_tax:
        taxable_gain = realized_year + loss_carry
        if taxable_gain > 0:
            tax = taxable_gain * SHORT_TERM_TAX
            values, basis = apply_tax_payment(values, basis, tax)
            tax_paid += tax
            curve[-1] = float(values.sum())
            loss_carry = 0.0
        else:
            loss_carry = taxable_gain
        final_value = float(values.sum())
        unrealized_gain = final_value - float(basis.sum())
        liquidation_taxable = unrealized_gain + loss_carry
        liquidation_tax = max(liquidation_taxable, 0.0) * SHORT_TERM_TAX
        after_liq_end_value = final_value - liquidation_tax

    years = len(target) / TRADING_DAYS
    label = "ALT L1>20% after-tax" if after_tax else "ALT L1>20% pre-tax"
    return CurveResult(
        label=label,
        curve=pd.Series(curve, index=target.index),
        rebalances=rebalances,
        turnover=turnover_sum / years,
        after_liq_end_value=after_liq_end_value,
    )


def buy_hold_curve(
    close: pd.DataFrame,
    weights: pd.Series,
    *,
    start: str,
    label: str,
) -> CurveResult:
    weights = normalize(weights[weights > 0])
    prices = close[weights.index].loc[start:].ffill().dropna()
    relatives = prices.div(prices.iloc[0])
    curve = relatives.mul(weights, axis=1).sum(axis=1) * ACCOUNT_VALUE
    end_value = float(curve.iloc[-1])
    gain = max(end_value - ACCOUNT_VALUE, 0.0)
    after_liq_end_value = end_value - gain * LONG_TERM_QQQ_LIQUIDATION_TAX
    return CurveResult(label=label, curve=curve, after_liq_end_value=after_liq_end_value)


def metrics(result: CurveResult) -> dict[str, float | int | str]:
    curve = result.curve.dropna()
    daily = curve.pct_change().dropna()
    years = len(curve) / TRADING_DAYS
    after_liq = result.after_liq_end_value
    return {
        "strategy": result.label,
        "cagr": (float(curve.iloc[-1]) / float(curve.iloc[0])) ** (1 / years) - 1,
        "after_liq_cagr": np.nan
        if after_liq is None
        else (after_liq / float(curve.iloc[0])) ** (1 / years) - 1,
        "max_drawdown": float((curve / curve.cummax() - 1).min()),
        "worst_12m": float(curve.pct_change(TRADING_DAYS).min()),
        "end_value": float(curve.iloc[-1]),
        "after_liq_end_value": np.nan if after_liq is None else after_liq,
        "rebalances": result.rebalances,
        "turnover": result.turnover,
        "daily_vol": float(daily.std() * np.sqrt(TRADING_DAYS)),
    }


def full_history_equal_weight(close: pd.DataFrame) -> tuple[pd.Series, list[str]]:
    prices = close[UNIVERSE].ffill().loc[START:]
    tickers = [ticker for ticker in UNIVERSE if pd.notna(prices[ticker].iloc[0])]
    return pd.Series(1.0 / len(tickers), index=tickers), tickers


def format_table(rows: list[dict[str, float | int | str]]) -> pd.DataFrame:
    table = pd.DataFrame(rows)
    out = table.copy()
    for col in ["cagr", "after_liq_cagr", "max_drawdown", "worst_12m", "daily_vol"]:
        out[col] = out[col].map(
            lambda x: "" if pd.isna(x) else f"{float(x) * 100:.1f}%"
        )
    for col in ["end_value", "after_liq_end_value"]:
        out[col] = out[col].map(
            lambda x: "" if pd.isna(x) else f"${float(x) / 1_000_000:.2f}M"
        )
    out["turnover"] = out["turnover"].map(lambda x: f"{float(x):.1f}x")
    return out


def plot_curves(results: list[CurveResult], path: Path, title: str) -> None:
    fig, ax = plt.subplots(figsize=(12, 7), dpi=170)
    for result in results:
        curve = result.curve.dropna()
        ax.plot(curve.index, curve / 1_000_000, label=result.label, linewidth=2)
    ax.set_title(title)
    ax.set_ylabel("Account value, $M")
    ax.set_yscale("log")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="upper left")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def plot_drawdowns(results: list[CurveResult], path: Path, title: str) -> None:
    fig, ax = plt.subplots(figsize=(12, 5), dpi=170)
    for result in results:
        curve = result.curve.dropna()
        drawdown = curve / curve.cummax() - 1.0
        ax.plot(drawdown.index, drawdown * 100, label=result.label, linewidth=2)
    ax.set_title(title)
    ax.set_ylabel("Drawdown")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="lower left")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    close, _, fundamentals = load()
    close, _ = add_gold_data(close, close)
    target = build_weights(close, fundamentals, 0.15, 0.50, "weekly")
    latest_target = normalize(target.iloc[-1])

    selected_pre = simulate_band_curve(close, target, start=START, band=0.20, after_tax=False)
    selected_tax = simulate_band_curve(close, target, start=START, band=0.20, after_tax=True)
    qqq = buy_hold_curve(
        close,
        pd.Series({"QQQ": 1.0}),
        start=START,
        label="QQQ buy-and-hold",
    )
    full_weights, full_tickers = full_history_equal_weight(close)
    full_equal = buy_hold_curve(
        close,
        full_weights,
        start=START,
        label="Equal-weight full-history AI/semis",
    )

    common_start = max(close[t].first_valid_index() for t in latest_target[latest_target > 0].index)
    common_start_text = str(common_start.date())
    common_selected = simulate_band_curve(
        close,
        target,
        start=common_start_text,
        band=0.20,
        after_tax=False,
    )
    common_selected = CurveResult(
        label="ALT L1>20% strategy",
        curve=common_selected.curve,
        rebalances=common_selected.rebalances,
        turnover=common_selected.turnover,
    )
    same_basket_static = buy_hold_curve(
        close,
        latest_target,
        start=common_start_text,
        label="Buy-hold current target basket",
    )
    same_basket_equal = buy_hold_curve(
        close,
        pd.Series(1.0, index=latest_target[latest_target > 0].index),
        start=common_start_text,
        label="Equal-weight current target names",
    )
    common_qqq = buy_hold_curve(
        close,
        pd.Series({"QQQ": 1.0}),
        start=common_start_text,
        label="QQQ buy-and-hold",
    )

    full_results = [selected_pre, selected_tax, qqq, full_equal]
    common_results = [common_selected, same_basket_static, same_basket_equal, common_qqq]

    OUT.mkdir(exist_ok=True)
    full_chart = OUT / "strategy_comparison_full_window.png"
    common_chart = OUT / "strategy_comparison_common_window.png"
    drawdown_chart = OUT / "strategy_comparison_drawdowns.png"
    plot_curves(full_results, full_chart, "Full Window: Strategy vs QQQ and AI/Semis Bracket")
    plot_curves(common_results, common_chart, "Common Window: Strategy vs Same Current Basket")
    plot_drawdowns(
        [selected_tax, qqq, full_equal],
        drawdown_chart,
        "Full Window Drawdowns: After-Tax Strategy vs Buy-Hold Benchmarks",
    )

    full_table = format_table([metrics(result) for result in full_results])
    common_table = format_table([metrics(result) for result in common_results])
    full_table.to_csv(OUT / "strategy_comparison_full_window_metrics.csv", index=False)
    common_table.to_csv(OUT / "strategy_comparison_common_window_metrics.csv", index=False)

    lines = [
        "# Strategy Comparison Charts",
        "",
        "Date: 2026-07-01",
        "",
        "## What This Compares",
        "",
        "- Full window: selected ALT 20% L1 band strategy versus QQQ "
        "and an equal-weight buy-and-hold basket of AI/semis names with "
        "full data from 2016-07-01.",
        "- Common window: selected ALT 20% L1 band strategy versus "
        f"buy-and-hold of the current target basket from {common_start_text}, "
        "the first date all current target names/proxies have data.",
        "- Current basket uses SNDK as the historical memory proxy for live DRAM.",
        "- Strategy after-tax curve uses annual 50% short-term tax payments "
        "deducted from portfolio value; liquidation uses the same 50% "
        "short-term rate.",
        "- Buy-and-hold curves are shown pre-liquidation, with an "
        "after-liquidation column using 33.1% long-term tax on gains.",
        "",
        "## Full Window Metrics",
        "",
        full_table.to_markdown(index=False),
        "",
        f"Full-history equal-weight tickers: `{', '.join(full_tickers)}`.",
        "",
        "## Common Current-Basket Window Metrics",
        "",
        common_table.to_markdown(index=False),
        "",
        "## Interpretation",
        "",
        "- Versus QQQ: yes. The selected strategy beats QQQ both pre-tax "
        "and after liquidation in this cached-data framework.",
        "- Versus a full-history equal-weight AI/semis buy-and-hold bracket: "
        "pre-tax yes, after-tax no. Buy-and-hold's tax deferral remains powerful.",
        "- Versus buy-and-hold of the exact current target basket: no on the "
        "short common window. The final winners exploded during that specific period.",
        "- The current-basket buy-and-hold result is not a 10-year proof; it "
        "is the exact survivorship problem the audit flagged.",
        "- The strategy's claimed edge is not magic asset selection alone. It "
        "comes from owning a biased AI/semis universe plus trend gates, GLD "
        "routing, and rebalance discipline. The universe choice remains the dominant bias.",
        "",
        "## Charts",
        "",
        f"- `{full_chart.name}`",
        f"- `{common_chart.name}`",
        f"- `{drawdown_chart.name}`",
    ]
    (OUT / "STRATEGY_COMPARISON_CHARTS.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
