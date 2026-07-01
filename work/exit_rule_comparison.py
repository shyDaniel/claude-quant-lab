from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yfinance as yf


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work"
OUT = ROOT / "outputs"
sys.path.append(str(WORK))

from medium_transform_grid import (  # noqa: E402
    ACCOUNT_VALUE,
    CACHE,
    START,
    TRADING_DAYS,
    UNIVERSE,
    load,
    sim,
    weights,
)
from nbis_storage_tilt_grid import BASE_ARGS, active_masks, overlay_weights  # noqa: E402
from smci_keep_backtest import SMCI_CURRENT_WEIGHT, apply_smci_floor  # noqa: E402


def calc_metrics(r: pd.Series, turn: float, start: str) -> dict[str, float]:
    returns = r.loc[start:].dropna()
    eq = (1 + returns).cumprod()
    years = len(returns) / TRADING_DAYS
    return {
        "cagr": eq.iloc[-1] ** (1 / years) - 1,
        "sharpe": returns.mean() / returns.std() * np.sqrt(TRADING_DAYS),
        "max_drawdown": (eq / eq.cummax() - 1).min(),
        "worst_12m": eq.pct_change(TRADING_DAYS).min(),
        "turnover": turn,
        "end_value": ACCOUNT_VALUE * eq.iloc[-1],
    }


def add_gold_data(close: pd.DataFrame, open_: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if "GLD" in close.columns and "GLD" in open_.columns:
        return close, open_
    cache_path = CACHE / "gld_prices.csv"
    if cache_path.exists():
        data = pd.read_csv(cache_path, parse_dates=["Date"], index_col="Date")
    else:
        data = yf.download("GLD", start="2015-01-01", auto_adjust=True, progress=False)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        data = data[["Open", "Close"]].dropna()
        data.index.name = "Date"
        data.to_csv(cache_path)
    close = close.copy()
    open_ = open_.copy()
    close["GLD"] = data["Close"].reindex(close.index).ffill()
    open_["GLD"] = data["Open"].reindex(open_.index).ffill()
    return close, open_


def current_final_weights(close: pd.DataFrame, fundamentals: pd.DataFrame) -> pd.DataFrame:
    base = weights(close, fundamentals, **BASE_ARGS)
    trend_active, tradable = active_masks(close)
    with_nbis = overlay_weights(base, trend_active, tradable, 0.25, 0.30, 1.0, "tradable")
    return apply_smci_floor(with_nbis, trend_active, tradable, SMCI_CURRENT_WEIGHT, "tradable")


def replace_defensive_asset(w: pd.DataFrame, defensive_asset: str) -> pd.DataFrame:
    out = w.copy()
    if defensive_asset == "BIL":
        return out
    if defensive_asset not in out.columns:
        out[defensive_asset] = 0.0
    out[defensive_asset] += out["BIL"]
    out["BIL"] = 0.0
    return out


def apply_exit_rules(
    w: pd.DataFrame,
    close: pd.DataFrame,
    *,
    individual_ma: int | None = None,
    basket_ma: int | None = None,
    trailing_window: int | None = None,
    trailing_drawdown: float | None = None,
    qqq_ma: int | None = None,
    defensive_asset: str = "BIL",
) -> pd.DataFrame:
    out = w.copy()
    if defensive_asset not in out.columns:
        out[defensive_asset] = 0.0
    px = close.reindex(out.index)
    ai_cols = [name for name in UNIVERSE if name in out.columns]
    blocked = pd.DataFrame(False, index=out.index, columns=ai_cols)

    if individual_ma is not None:
        ma = px[ai_cols].rolling(individual_ma).mean()
        has_history = px[ai_cols].rolling(individual_ma).count().ge(individual_ma)
        blocked |= ~((px[ai_cols] > ma) & has_history)

    if basket_ma is not None:
        basket = (1 + px[ai_cols].pct_change().mean(axis=1).fillna(0)).cumprod()
        basket_ok = basket > basket.rolling(basket_ma).mean()
        blocked |= pd.DataFrame(
            np.repeat((~basket_ok).to_numpy()[:, None], len(ai_cols), axis=1),
            index=out.index,
            columns=ai_cols,
        )

    if trailing_window is not None and trailing_drawdown is not None:
        high = px[ai_cols].rolling(trailing_window).max()
        has_history = px[ai_cols].rolling(trailing_window).count().ge(trailing_window)
        blocked |= ~((px[ai_cols] / high >= 1 - trailing_drawdown) & has_history)

    removed = out[ai_cols].where(blocked, 0).sum(axis=1)
    out[ai_cols] = out[ai_cols].mask(blocked, 0)

    if qqq_ma is not None:
        qqq_ok = (px["QQQ"] > px["QQQ"].rolling(qqq_ma).mean()) & px["QQQ"].rolling(qqq_ma).count().ge(qqq_ma)
        removed += out["QQQ"].where(~qqq_ok, 0)
        out.loc[~qqq_ok, "QQQ"] = 0

    out[defensive_asset] += removed
    return out


def buy_and_hold_returns(close: pd.DataFrame, target: pd.Series, start: str) -> pd.Series:
    tickers = target[target > 0].index.tolist()
    prices = close[tickers].loc[start:].dropna()
    start_prices = prices.iloc[0]
    wealth = prices.div(start_prices).mul(target[tickers], axis=1).sum(axis=1)
    return wealth.pct_change().fillna(0)


def add_exit_grid(
    variants: dict[str, pd.DataFrame],
    w: pd.DataFrame,
    close: pd.DataFrame,
    defensive_asset: str,
    prefix: str,
) -> None:
    for ma in [50, 75, 100, 150, 200]:
        variants[f"{prefix}_all_ai_individual_{ma}dma_exit"] = apply_exit_rules(
            w,
            close,
            individual_ma=ma,
            defensive_asset=defensive_asset,
        )
    for ma in [50, 100, 150, 200]:
        variants[f"{prefix}_all_ai_basket_{ma}dma_exit"] = apply_exit_rules(
            w,
            close,
            basket_ma=ma,
            defensive_asset=defensive_asset,
        )
    for ma in [50, 100, 150, 200]:
        variants[f"{prefix}_all_ai_individual{ma}_or_basket{ma}_exit"] = apply_exit_rules(
            w,
            close,
            individual_ma=ma,
            basket_ma=ma,
            defensive_asset=defensive_asset,
        )
    for window in [21, 63, 126]:
        for drawdown in [0.10, 0.15, 0.20, 0.25]:
            pct = int(drawdown * 100)
            variants[f"{prefix}_all_ai_{pct}pct_from_{window}d_high_exit"] = apply_exit_rules(
                w,
                close,
                trailing_window=window,
                trailing_drawdown=drawdown,
                defensive_asset=defensive_asset,
            )
    for qqq_ma in [100, 200]:
        variants[f"{prefix}_all_ai_individual100_plus_qqq{qqq_ma}_exit"] = apply_exit_rules(
            w,
            close,
            individual_ma=100,
            qqq_ma=qqq_ma,
            defensive_asset=defensive_asset,
        )


def strategy_table(
    close: pd.DataFrame,
    open_: pd.DataFrame,
    fundamentals: pd.DataFrame,
    w: pd.DataFrame,
) -> pd.DataFrame:
    trend_active, tradable = active_masks(close)
    gld_w = replace_defensive_asset(w, "GLD")
    variants: dict[str, pd.DataFrame] = {
        "current_weekly_rebalance_BIL_defensive": w,
        "current_weekly_rebalance_GLD_defensive": gld_w,
    }
    add_exit_grid(variants, w, close, "BIL", "BIL")
    add_exit_grid(variants, gld_w, close, "GLD", "GLD")

    # This is close to the original floor discipline: conviction floors exist only when the
    # name passes the same 100-day trend gate as the rest of the basket.
    base = weights(close, fundamentals, **BASE_ARGS)
    trend_gated = overlay_weights(base, trend_active, tradable, 0.25, 0.30, 1.0, "trend_gated")
    floors_obey = apply_smci_floor(
        trend_gated,
        trend_active,
        tradable,
        SMCI_CURRENT_WEIGHT,
        "trend_gated",
    )
    variants["BIL_floors_obey_100dma_gate"] = floors_obey
    variants["GLD_floors_obey_100dma_gate"] = replace_defensive_asset(floors_obey, "GLD")

    rows = []
    for name, candidate in variants.items():
        daily, turn = sim(close, open_, candidate, "close")
        rows.append({"strategy": name, "window": "2016-07-01_to_today", **calc_metrics(daily, turn, START)})
    return pd.DataFrame(rows), variants


def common_window_table(
    close: pd.DataFrame,
    open_: pd.DataFrame,
    variants: dict[str, pd.DataFrame],
) -> tuple[pd.DataFrame, str]:
    latest = variants["current_weekly_rebalance_GLD_defensive"].iloc[-1]
    target = latest[latest > 0]
    common_start = max(close[t].first_valid_index() for t in target.index)
    start = str(common_start.date())
    rows = []
    bh = buy_and_hold_returns(close, target, start)
    rows.append({"strategy": "static_buy_once_no_rebalance", "window": f"{start}_to_today", **calc_metrics(bh, 0.0, start)})
    for name, candidate in variants.items():
        daily, turn = sim(close, open_, candidate, "close")
        rows.append({"strategy": name, "window": f"{start}_to_today", **calc_metrics(daily, turn, start)})
    return pd.DataFrame(rows), start


def plot_common(
    close: pd.DataFrame,
    open_: pd.DataFrame,
    variants: dict[str, pd.DataFrame],
    start: str,
) -> Path:
    latest = variants["current_weekly_rebalance_GLD_defensive"].iloc[-1]
    target = latest[latest > 0]
    curves: dict[str, pd.Series] = {}
    bh = buy_and_hold_returns(close, target, start)
    curves["static buy once"] = (1 + bh.loc[start:]).cumprod()
    selected = {
        "weekly GLD defensive": "current_weekly_rebalance_GLD_defensive",
        "GLD 100dma exit": "GLD_all_ai_individual_100dma_exit",
        "GLD combined 100dma/basket": "GLD_all_ai_individual100_or_basket100_exit",
        "GLD floors obey 100dma": "GLD_floors_obey_100dma_gate",
    }
    for label, name in selected.items():
        daily, _ = sim(close, open_, variants[name], "close")
        curves[label] = (1 + daily.loc[start:]).cumprod()

    fig, ax = plt.subplots(figsize=(11, 6), dpi=160)
    for label, curve in curves.items():
        ax.plot(curve.index, curve, label=label)
    ax.set_yscale("log")
    ax.set_title("Rebalance vs Downturn-Exit Rules")
    ax.set_ylabel("Log scale wealth, $1 initial")
    ax.grid(True, alpha=0.25)
    ax.legend()
    chart = OUT / "exit_rule_comparison_chart.png"
    fig.savefig(chart, bbox_inches="tight")
    return chart


def write_report(full: pd.DataFrame, common: pd.DataFrame, start: str, chart: Path) -> None:
    full_sorted = full.sort_values(["cagr", "sharpe"], ascending=False)
    common_sorted = common.sort_values(["cagr", "sharpe"], ascending=False)
    lines = [
        "# Exit Rule Comparison",
        "",
        "Date: 2026-07-01",
        "",
        "## Correction",
        "",
        "The selected strategy had two different mechanisms mixed together: non-floor AI positions used trend gates, while NBIS and SMCI conviction floors were allowed to stay as target-weight positions. This report compares that against explicit sell-to-avoid-downturn variants and replaces the defensive bucket with GLD/gold variants.",
        "",
        "## Long Framework Window",
        "",
        full_sorted.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Common Window Including Current Target Names",
        "",
        f"Common start: {start}. This is the clean comparison for static no-rebalance because NBIS/SNDK proxy do not have full 10-year histories.",
        "",
        common_sorted.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Interpretation",
        "",
        "- Daily close-to-close is the return measurement, not necessarily the rebalance rule.",
        "- The prior chosen strategy was not a pure downturn-avoidance strategy for NBIS/SMCI. It was trend-gated for non-floor AI names and target-weight rebalanced for NBIS/SMCI floors.",
        "- GLD variants replace the BIL/cash defensive sleeve and route exit proceeds into gold.",
        "- In this dataset, the weekly current strategy still beat the 100-day hard-exit variants on CAGR in the long framework window.",
        "- Hard 100-day exits reduced some risk in some windows but also created more whipsaw and did not clearly dominate.",
        "- Static buy-once/no-rebalance is only testable on the shorter common window and should not be treated as a 10-year proof.",
        "",
        f"Chart: `{chart.name}`",
    ]
    (OUT / "EXIT_RULE_COMPARISON.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    close, open_, fundamentals = load()
    close, open_ = add_gold_data(close, open_)
    w = current_final_weights(close, fundamentals)
    full, variants = strategy_table(close, open_, fundamentals, w)
    common, start = common_window_table(close, open_, variants)
    chart = plot_common(close, open_, variants, start)
    full.to_csv(OUT / "exit_rule_comparison_full_results.csv", index=False)
    common.to_csv(OUT / "exit_rule_comparison_common_window_results.csv", index=False)
    write_report(full, common, start, chart)


if __name__ == "__main__":
    main()
