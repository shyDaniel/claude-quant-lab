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

from exit_rule_comparison import add_gold_data  # noqa: E402
from medium_transform_grid import ACCOUNT_VALUE, START, TRADING_DAYS, UNIVERSE, load  # noqa: E402
from nbis_redirect_sensitivity import build_weights  # noqa: E402


ST_TAX = 0.50
LT_TAX = 0.331
COST_BPS = 10.0
THRESHOLDS = [0.10, 0.15, 0.20, 0.25]
CADENCES = ["weekly", "monthly"]
HIGH_WINDOW = 252


@dataclass(frozen=True)
class Lot:
    shares: float
    basis_per_share: float
    acquired: pd.Timestamp


@dataclass(frozen=True)
class GateResult:
    strategy: str
    threshold: float | None
    cadence: str
    pre_tax_cagr: float
    after_liq_cagr: float
    max_drawdown_pre_tax: float
    worst_12m_pre_tax: float
    after_tax_curve_max_drawdown: float
    trades: int
    round_trips: float
    st_realized: float
    lt_realized: float
    tax_paid: float
    liquidation_tax: float
    end_pre_tax: float
    end_after_tax_pre_liq: float
    end_after_tax_after_liq: float


def normalize(weights: pd.Series) -> pd.Series:
    out = weights.fillna(0.0).clip(lower=0.0)
    total = float(out.sum())
    if total <= 0:
        raise ValueError("Weights sum to zero")
    return out / total


def cagr(start_value: float, end_value: float, periods: int) -> float:
    years = periods / TRADING_DAYS
    return (end_value / start_value) ** (1 / years) - 1


def max_drawdown(curve: pd.Series) -> float:
    return float((curve / curve.cummax() - 1.0).min())


def worst_12m(curve: pd.Series) -> float:
    return float(curve.pct_change(TRADING_DAYS).min())


def rebalance_mask(index: pd.DatetimeIndex, cadence: str) -> pd.Series:
    if cadence == "weekly":
        grouped = [index.isocalendar().year, index.isocalendar().week]
        return index.to_series().groupby(grouped).transform("max") == index
    if cadence == "monthly":
        return index.to_series().groupby(index.to_period("M")).transform("max") == index
    raise ValueError(cadence)


def full_history_equal_weight_index(close: pd.DataFrame) -> tuple[pd.Series, list[str]]:
    prices = close[UNIVERSE].loc[START:].ffill()
    tickers = [ticker for ticker in UNIVERSE if pd.notna(prices[ticker].iloc[0])]
    weights = pd.Series(1.0 / len(tickers), index=tickers)
    relatives = prices[tickers].div(prices[tickers].iloc[0])
    index = relatives.mul(weights, axis=1).sum(axis=1)
    return index.dropna(), tickers


def current_target_index(close: pd.DataFrame, fundamentals: pd.DataFrame) -> pd.Series:
    target = normalize(build_weights(close, fundamentals, 0.15, 0.50, "weekly").iloc[-1])
    target = target[target > 0]
    prices = close[target.index].ffill().dropna()
    relatives = prices.div(prices.iloc[0])
    return relatives.mul(target, axis=1).sum(axis=1)


def pay_tax_from_lots(lots: list[Lot], price: float, tax: float, date: pd.Timestamp) -> list[Lot]:
    if tax <= 0:
        return lots
    value = sum(lot.shares * price for lot in lots)
    if value <= 0:
        return []
    scale = max((value - tax) / value, 0.0)
    return [Lot(lot.shares * scale, lot.basis_per_share, lot.acquired) for lot in lots]


def sell_lots(
    lots: list[Lot],
    price: float,
    date: pd.Timestamp,
) -> tuple[float, float, float]:
    st_gain = 0.0
    lt_gain = 0.0
    proceeds = 0.0
    for lot in lots:
        lot_proceeds = lot.shares * price
        gain = lot_proceeds - lot.shares * lot.basis_per_share
        if (date - lot.acquired).days >= 365:
            lt_gain += gain
        else:
            st_gain += gain
        proceeds += lot_proceeds
    return proceeds, st_gain, lt_gain


def annual_tax(
    st_gain: float,
    lt_gain: float,
    loss_carry: float,
) -> tuple[float, float]:
    st_pos = max(st_gain, 0.0)
    lt_pos = max(lt_gain, 0.0)
    losses = max(-st_gain, 0.0) + max(-lt_gain, 0.0) + max(-loss_carry, 0.0)

    st_offset = min(st_pos, losses)
    st_pos -= st_offset
    losses -= st_offset

    lt_offset = min(lt_pos, losses)
    lt_pos -= lt_offset
    losses -= lt_offset

    tax = st_pos * ST_TAX + lt_pos * LT_TAX
    return tax, -losses


def after_liquidation_value(
    lots: list[Lot],
    price: float,
    date: pd.Timestamp,
    loss_carry: float,
) -> tuple[float, float]:
    value, st_gain, lt_gain = sell_lots(lots, price, date)
    tax, _ = annual_tax(st_gain, lt_gain, loss_carry)
    return value - tax, tax


def simulate_buy_hold(
    basket: pd.Series,
    *,
    label: str = "Buy-hold EW-9",
) -> GateResult:
    basket = basket.loc[START:].dropna()
    curve = ACCOUNT_VALUE * basket / float(basket.iloc[0])
    end_after_liq, liquidation_tax = after_liquidation_value(
        [Lot(ACCOUNT_VALUE / float(basket.iloc[0]), float(basket.iloc[0]), basket.index[0])],
        float(basket.iloc[-1]),
        basket.index[-1],
        0.0,
    )
    periods = len(curve)
    return GateResult(
        strategy=label,
        threshold=None,
        cadence="none",
        pre_tax_cagr=cagr(ACCOUNT_VALUE, float(curve.iloc[-1]), periods),
        after_liq_cagr=cagr(ACCOUNT_VALUE, end_after_liq, periods),
        max_drawdown_pre_tax=max_drawdown(curve),
        worst_12m_pre_tax=worst_12m(curve),
        after_tax_curve_max_drawdown=max_drawdown(curve),
        trades=0,
        round_trips=0.0,
        st_realized=0.0,
        lt_realized=0.0,
        tax_paid=0.0,
        liquidation_tax=liquidation_tax,
        end_pre_tax=float(curve.iloc[-1]),
        end_after_tax_pre_liq=float(curve.iloc[-1]),
        end_after_tax_after_liq=end_after_liq,
    )


def gate_state(
    basket_value: float,
    rolling_high: float,
    threshold: float,
) -> bool:
    return basket_value >= rolling_high * (1.0 - threshold)


def simulate_gate(
    basket: pd.Series,
    gld: pd.Series,
    *,
    threshold: float,
    cadence: str,
) -> tuple[GateResult, pd.DataFrame, pd.Series, pd.Series]:
    frame = pd.DataFrame({"basket": basket, "gld": gld}).ffill().dropna().loc[START:]
    basket_index = frame["basket"]
    gld_index = frame["gld"]
    rolling_high = basket_index.rolling(HIGH_WINDOW, min_periods=1).max()
    checks = rebalance_mask(frame.index, cadence)

    pre_asset = "basket"
    tax_asset = "basket"
    pre_value = ACCOUNT_VALUE
    lots = [
        Lot(
            ACCOUNT_VALUE / float(basket_index.iloc[0]),
            float(basket_index.iloc[0]),
            frame.index[0],
        )
    ]

    pre_curve = []
    after_curve = []
    trades: list[dict[str, float | str | pd.Timestamp]] = []
    st_year = 0.0
    lt_year = 0.0
    loss_carry = 0.0
    st_total = 0.0
    lt_total = 0.0
    tax_paid = 0.0
    prev_year = frame.index[0].year
    prev_prices = {"basket": float(basket_index.iloc[0]), "gld": float(gld_index.iloc[0])}

    for pos, date in enumerate(frame.index):
        prices = {"basket": float(basket_index.iloc[pos]), "gld": float(gld_index.iloc[pos])}
        if pos > 0:
            pre_value *= prices[pre_asset] / prev_prices[pre_asset]

        if pos > 0 and date.year != prev_year:
            tax, loss_carry = annual_tax(st_year, lt_year, loss_carry)
            if tax > 0:
                lots = pay_tax_from_lots(lots, prev_prices[tax_asset], tax, date)
                tax_paid += tax
            st_year = 0.0
            lt_year = 0.0
            prev_year = date.year

        if bool(checks.iloc[pos]):
            is_safe = gate_state(
                float(basket_index.iloc[pos]),
                float(rolling_high.iloc[pos]),
                threshold,
            )
            target_asset = "basket" if is_safe else "gld"
            if target_asset != pre_asset:
                pre_value *= 1.0 - COST_BPS / 10_000.0
                pre_asset = target_asset

                current_price = prices[tax_asset]
                proceeds, st_gain, lt_gain = sell_lots(lots, current_price, date)
                proceeds *= 1.0 - COST_BPS / 10_000.0
                st_year += st_gain
                lt_year += lt_gain
                st_total += st_gain
                lt_total += lt_gain

                new_price = prices[target_asset]
                lots = [Lot(proceeds / new_price, new_price, date)]
                trades.append(
                    {
                        "date": date,
                        "action": f"{tax_asset}_to_{target_asset}",
                        "basket_drawdown_from_1y_high": prices["basket"]
                        / float(rolling_high.iloc[pos])
                        - 1.0,
                        "st_gain": st_gain,
                        "lt_gain": lt_gain,
                        "portfolio_value": proceeds,
                    }
                )
                tax_asset = target_asset

        current_after_value = sum(lot.shares * prices[tax_asset] for lot in lots)
        pre_curve.append(pre_value)
        after_curve.append(current_after_value)
        prev_prices = prices

    tax, loss_carry = annual_tax(st_year, lt_year, loss_carry)
    if tax > 0:
        lots = pay_tax_from_lots(lots, prev_prices[tax_asset], tax, frame.index[-1])
        tax_paid += tax

    final_after_pre_liq = sum(lot.shares * prev_prices[tax_asset] for lot in lots)
    final_after_liq, liquidation_tax = after_liquidation_value(
        lots,
        prev_prices[tax_asset],
        frame.index[-1],
        loss_carry,
    )

    pre_series = pd.Series(pre_curve, index=frame.index)
    after_series = pd.Series(after_curve, index=frame.index)
    periods = len(frame)
    result = GateResult(
        strategy=f"{cadence}_gate_{int(threshold * 100)}pct",
        threshold=threshold,
        cadence=cadence,
        pre_tax_cagr=cagr(ACCOUNT_VALUE, float(pre_series.iloc[-1]), periods),
        after_liq_cagr=cagr(ACCOUNT_VALUE, final_after_liq, periods),
        max_drawdown_pre_tax=max_drawdown(pre_series),
        worst_12m_pre_tax=worst_12m(pre_series),
        after_tax_curve_max_drawdown=max_drawdown(after_series),
        trades=len(trades),
        round_trips=len(trades) / 2.0,
        st_realized=st_total,
        lt_realized=lt_total,
        tax_paid=tax_paid,
        liquidation_tax=liquidation_tax,
        end_pre_tax=float(pre_series.iloc[-1]),
        end_after_tax_pre_liq=final_after_pre_liq,
        end_after_tax_after_liq=final_after_liq,
    )
    return result, pd.DataFrame(trades), pre_series, after_series


def result_row(result: GateResult) -> dict[str, float | str | int]:
    return {
        "strategy": result.strategy,
        "threshold": "" if result.threshold is None else result.threshold,
        "cadence": result.cadence,
        "pre_tax_cagr": result.pre_tax_cagr,
        "after_liq_cagr": result.after_liq_cagr,
        "max_drawdown_pre_tax": result.max_drawdown_pre_tax,
        "worst_12m_pre_tax": result.worst_12m_pre_tax,
        "after_tax_curve_max_drawdown": result.after_tax_curve_max_drawdown,
        "trades": result.trades,
        "round_trips": result.round_trips,
        "st_realized": result.st_realized,
        "lt_realized": result.lt_realized,
        "tax_paid": result.tax_paid,
        "liquidation_tax": result.liquidation_tax,
        "end_pre_tax": result.end_pre_tax,
        "end_after_tax_pre_liq": result.end_after_tax_pre_liq,
        "end_after_tax_after_liq": result.end_after_tax_after_liq,
    }


def format_results(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    for col in [
        "pre_tax_cagr",
        "after_liq_cagr",
        "max_drawdown_pre_tax",
        "worst_12m_pre_tax",
        "after_tax_curve_max_drawdown",
    ]:
        if col in out.columns:
            out[col] = out[col].map(lambda x: f"{float(x) * 100:.1f}%")
    for col in ["end_pre_tax", "end_after_tax_after_liq"]:
        out[col] = out[col].map(lambda x: f"${float(x) / 1_000_000:.2f}M")
    return out


def plot_curves(curves: dict[str, pd.Series], path: Path, title: str) -> None:
    fig, ax = plt.subplots(figsize=(12, 7), dpi=170)
    for label, curve in curves.items():
        ax.plot(curve.index, curve / 1_000_000.0, label=label, linewidth=2)
    ax.set_title(title)
    ax.set_ylabel("Account value, $M")
    ax.set_yscale("log")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="upper left")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def plot_sweep(results: pd.DataFrame, path: Path) -> None:
    gated = results[results["threshold"] != ""].copy()
    fig, ax = plt.subplots(figsize=(11, 6), dpi=170)
    for cadence in CADENCES:
        data = gated[gated["cadence"] == cadence].copy()
        ax.plot(
            data["threshold"].astype(float) * 100,
            data["pre_tax_cagr"] * 100,
            marker="o",
            label=f"{cadence} pre-tax",
        )
        ax.plot(
            data["threshold"].astype(float) * 100,
            data["after_liq_cagr"] * 100,
            marker="s",
            linestyle="--",
            label=f"{cadence} after-liq",
        )
    ax.set_title("Catastrophe Gate Sweep")
    ax.set_xlabel("Exit threshold below trailing 1y high")
    ax.set_ylabel("CAGR")
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def extension_stats(idx: pd.Series) -> dict[str, float | str]:
    ma = idx.rolling(200).mean()
    latest = float(idx.iloc[-1])
    latest_ma = float(ma.iloc[-1])
    return {
        "date": str(idx.index[-1].date()),
        "vs_200dma": latest / latest_ma - 1.0,
        "basket_index": latest,
        "basket_200dma": latest_ma,
    }


def main() -> None:
    close, _, fundamentals = load()
    close, _ = add_gold_data(close, close)
    basket, tickers = full_history_equal_weight_index(close)
    gld = close["GLD"].loc[basket.index].ffill()

    rows: list[dict[str, float | str | int]] = []
    trade_logs: list[pd.DataFrame] = []
    curves: dict[str, pd.Series] = {}

    buy_hold = simulate_buy_hold(basket)
    rows.append(result_row(buy_hold))
    curves["buy-hold EW-9"] = ACCOUNT_VALUE * basket.loc[START:] / float(basket.loc[START:].iloc[0])

    selected_log = pd.DataFrame()
    for cadence in CADENCES:
        for threshold in THRESHOLDS:
            result, trades, pre_curve, after_curve = simulate_gate(
                basket,
                gld,
                threshold=threshold,
                cadence=cadence,
            )
            rows.append(result_row(result))
            if not trades.empty:
                trades = trades.copy()
                trades.insert(0, "strategy", result.strategy)
                trade_logs.append(trades)
            if cadence == "monthly" and threshold == 0.15:
                curves["15% monthly gate pre-tax"] = pre_curve
                curves["15% monthly gate after-tax curve"] = after_curve
                selected_log = trades

    results = pd.DataFrame(rows)
    trades_all = pd.concat(trade_logs, ignore_index=True) if trade_logs else pd.DataFrame()
    ew9_extension = extension_stats(basket)
    current_extension = extension_stats(current_target_index(close, fundamentals))

    OUT.mkdir(exist_ok=True)
    results.to_csv(OUT / "catastrophe_gate_sweep_results.csv", index=False)
    trades_all.to_csv(OUT / "catastrophe_gate_trade_log.csv", index=False)

    chart = OUT / "catastrophe_gate_curves.png"
    sweep_chart = OUT / "catastrophe_gate_sweep.png"
    plot_curves(curves, chart, "EW-9 Buy-and-Hold vs 15% Monthly Catastrophe Gate")
    plot_sweep(results, sweep_chart)

    display_cols = [
        "strategy",
        "pre_tax_cagr",
        "after_liq_cagr",
        "max_drawdown_pre_tax",
        "worst_12m_pre_tax",
        "after_tax_curve_max_drawdown",
        "trades",
        "end_pre_tax",
        "end_after_tax_after_liq",
    ]
    display = format_results(results[display_cols])

    selected_display = selected_log.copy()
    if not selected_display.empty:
        selected_display["date"] = pd.to_datetime(selected_display["date"]).dt.date.astype(str)
        selected_display["basket_drawdown_from_1y_high"] = selected_display[
            "basket_drawdown_from_1y_high"
        ].map(lambda x: f"{x * 100:.1f}%")
        selected_display["portfolio_value"] = selected_display["portfolio_value"].map(
            lambda x: f"${x / 1_000_000:.2f}M"
        )
        selected_display = selected_display[
            ["date", "action", "basket_drawdown_from_1y_high", "portfolio_value"]
        ]

    lines = [
        "# Catastrophe Gate Buy-and-Hold Sweep",
        "",
        "Date: 2026-07-01",
        "",
        "## Method",
        "",
        "- Basket: equal-weight full-history AI/semis names with valid data at 2016-07-01.",
        f"- Tickers: `{', '.join(tickers)}`.",
        "- Gate: hold the basket unless it closes more than threshold below "
        "its trailing 252-trading-day high; then switch to GLD.",
        "- Re-entry: switch back when the basket is back within the same "
        "threshold of its trailing 252-trading-day high.",
        "- Sweep: thresholds 10%, 15%, 20%, 25%; weekly and monthly checks.",
        "- Taxes: lot-level synthetic-basket/GLD accounting with 50% ST tax, "
        "33.1% LT tax, annual tax payment, and final liquidation tax.",
        "",
        "## Results",
        "",
        display.to_markdown(index=False),
        "",
        "## 15% Monthly Gate Trade Log",
        "",
        selected_display.to_markdown(index=False) if not selected_display.empty else "No trades.",
        "",
        "## Current Target Basket Extension",
        "",
        f"- Cached date: `{ew9_extension['date']}`.",
        f"- EW-9 full-history basket vs 200dma: `{float(ew9_extension['vs_200dma']) * 100:.1f}%`.",
        f"- Current target basket vs 200dma: `{float(current_extension['vs_200dma']) * 100:.1f}%`.",
        "- The EW-9 number is the one that matches Claude's `+41.6%`; the "
        "current target basket is more extended because it includes "
        "NBIS/SNDK/GEV and today's target weights.",
        "",
        "## Interpretation",
        "",
        "- Claude's corrected taxable-account conclusion is directionally "
        "right: buy-and-hold wins after liquidation against the gate in this "
        "taxable model.",
        "- The 15% monthly gate improves pre-tax return and sharply reduces "
        "drawdown, but taxes turn that protection into an after-tax return drag.",
        "- Weekly gates trade more often and are not clearly worth the added churn.",
        "- In taxable, the gate is insurance. In a sheltered account, the same "
        "gate is much more attractive because the pre-tax result matters.",
        "- The current target basket is extended versus its 200-day average in "
        "the cached data, so regret-control tranching is psychologically "
        "reasonable even though rolling entry tests usually favor lump sum.",
        "",
        "## Charts",
        "",
        f"- `{chart.name}`",
        f"- `{sweep_chart.name}`",
    ]
    (OUT / "CATASTROPHE_GATE_BUY_HOLD.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
