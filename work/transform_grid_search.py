from __future__ import annotations

import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "work" / "cache"
OUT = ROOT / "outputs"
os.environ.setdefault("MPLCONFIGDIR", str(CACHE / "mpl"))

UNIVERSE = [
    "NVDA",
    "AMD",
    "AVGO",
    "INTC",
    "MU",
    "SNDK",
    "MRVL",
    "STX",
    "ANET",
    "VST",
    "CEG",
    "GEV",
    "VRT",
    "NBIS",
    "SMCI",
]
ACCOUNT_VALUE = 278_726.16
AI_SLEEVE = 0.70
QQQ_WEIGHT = 0.25
CASH_WEIGHT = 0.05
START = "2016-07-01"
TRADING_DAYS = 252
CURRENT_VALUES = {
    "QQQ": 100.00 * 728.39,
    "NBIS": 120.00 * 234.92,
    "MU": 25.00 * 1063.06,
    "DRAM": 300.01 * 67.02,
    "NVDA": 100.01 * 199.53,
    "SMCI": 300.00 * 28.16,
    "CASH": 102_555.39,
}


def pct_score(series: pd.Series, neutral: float = 0.55) -> pd.Series:
    return series.replace([np.inf, -np.inf], np.nan).rank(pct=True).fillna(neutral).clip(0.05, 1.0)


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    close = pd.read_csv(CACHE / "grid_prices.csv", parse_dates=["Date"], index_col="Date")
    open_ = pd.read_csv(CACHE / "grid_open_prices.csv", parse_dates=["Date"], index_col="Date")
    f = pd.read_csv(CACHE / "grid_fundamentals_raw.csv").set_index("ticker")
    f["cap_rank"] = pct_score(np.log(f["market_cap"].clip(lower=1.0)))
    f["earnings_growth_score"] = pct_score(f["earnings_quarterly_growth"].clip(-1.0, 3.0))
    f["revenue_growth_score"] = pct_score(f["revenue_growth"].clip(-1.0, 2.0))
    f["margin_score"] = pct_score(f["profit_margins"].clip(-1.0, 1.0))
    f["roe_score"] = pct_score(f["return_on_equity"].clip(-2.0, 3.0))
    f["eps_score"] = pct_score(f["forward_eps"].fillna(f["trailing_eps"]).clip(-100, 500))
    f["earnings_score"] = (
        0.35 * f["earnings_growth_score"]
        + 0.25 * f["revenue_growth_score"]
        + 0.20 * f["margin_score"]
        + 0.10 * f["roe_score"]
        + 0.10 * f["eps_score"]
    ).clip(0.05, 1.0)
    return close, open_, f


def size_score(fundamentals: pd.DataFrame, transform: str) -> pd.Series:
    cap = fundamentals.reindex(UNIVERSE)["market_cap"].astype(float).clip(lower=1.0)
    rank = fundamentals.reindex(UNIVERSE)["cap_rank"].fillna(0.55)
    if transform == "equal":
        raw = pd.Series(1.0, index=UNIVERSE)
    elif transform == "cap_rank":
        raw = rank
    elif transform == "sqrt_cap_rank":
        raw = rank ** 0.5
    elif transform == "quarter_cap_rank":
        raw = rank ** 0.25
    elif transform == "raw_cap":
        raw = cap / cap.median()
    elif transform == "sqrt_raw_cap":
        raw = (cap / cap.median()) ** 0.5
    elif transform == "log_cap":
        raw = np.log(cap) / np.log(cap).median()
    elif transform == "small_tilt":
        raw = (1.05 - rank).clip(0.05, 1.0)
    elif transform == "sqrt_small_tilt":
        raw = (1.05 - rank).clip(0.05, 1.0) ** 0.5
    elif transform == "barbell":
        raw = (rank - 0.5).abs() * 2 + 0.10
    else:
        raise ValueError(transform)
    return raw.fillna(1.0).clip(0.01, None)


def earnings_score(fundamentals: pd.DataFrame, transform: str) -> pd.Series:
    base = fundamentals.reindex(UNIVERSE)["earnings_score"].fillna(0.55).clip(0.05, 1.0)
    growth = fundamentals.reindex(UNIVERSE)["earnings_growth_score"].fillna(0.55).clip(0.05, 1.0)
    margin = fundamentals.reindex(UNIVERSE)["margin_score"].fillna(0.55).clip(0.05, 1.0)
    if transform == "none":
        return pd.Series(1.0, index=UNIVERSE)
    if transform == "sqrt":
        return base ** 0.5
    if transform == "linear":
        return base
    if transform == "square":
        return base ** 2
    if transform == "growth_only":
        return growth
    if transform == "quality_growth":
        return (0.65 * base + 0.35 * margin).clip(0.05, 1.0)
    raise ValueError(transform)


def cap_row(row: pd.Series, max_weight: float) -> pd.Series:
    row = row.astype(float).clip(lower=0.0)
    if row.sum() <= 0:
        return row
    w = row / row.sum()
    active = w > 0
    cap = max(max_weight, 1.0 / active.sum())
    for _ in range(15):
        over = w > cap
        if not over.any():
            break
        excess = (w.loc[over] - cap).sum()
        w.loc[over] = cap
        under = active & ~over
        if not under.any() or excess <= 0:
            break
        w.loc[under] += excess * w.loc[under] / w.loc[under].sum()
    return w / w.sum()


def rebalance_mask(index: pd.DatetimeIndex, cadence: str) -> pd.Series:
    if cadence == "weekly":
        return index.to_series().groupby([index.isocalendar().year, index.isocalendar().week]).transform("max") == index
    return index.to_series().groupby(index.to_period("M")).transform("max") == index


def build_weights(
    close: pd.DataFrame,
    fundamentals: pd.DataFrame,
    size_transform: str,
    size_power: float,
    earn_transform: str,
    earn_power: float,
    momentum_power: float,
    max_weight: float,
    cadence: str,
) -> pd.DataFrame:
    px = close[UNIVERSE].dropna(how="all")
    above = px > px.rolling(100).mean()
    valid = px.rolling(126).count().ge(126)
    basket_nav = (1 + px.pct_change().mean(axis=1).fillna(0)).cumprod()
    gate = basket_nav > basket_nav.rolling(100).mean()
    active = (above & valid).mul(gate, axis=0)

    size = size_score(fundamentals, size_transform) ** size_power
    earn = earnings_score(fundamentals, earn_transform) ** earn_power
    mom = (px / px.shift(126) - 1).rank(axis=1, pct=True).fillna(0.5).clip(0.05, 1.0) ** momentum_power
    raw = active.astype(float).mul(size * earn, axis=1) * mom

    rebal = rebalance_mask(raw.index, cadence)
    ai = pd.DataFrame(np.nan, index=raw.index, columns=UNIVERSE)
    capped = raw.loc[rebal].apply(lambda row: cap_row(row, max_weight), axis=1)
    ai.loc[rebal] = capped
    ai = ai.ffill().fillna(0.0) * AI_SLEEVE
    weights = ai.copy()
    weights["QQQ"] = QQQ_WEIGHT
    weights["BIL"] = CASH_WEIGHT + (AI_SLEEVE - ai.sum(axis=1))
    return weights


def return_matrix(close: pd.DataFrame, open_: pd.DataFrame, weights: pd.DataFrame, mode: str) -> pd.DataFrame:
    c = close.reindex(weights.index)[weights.columns]
    o = open_.reindex(weights.index)[weights.columns]
    if mode == "overnight":
        return (o / c.shift(1) - 1).fillna(0.0)
    if mode == "intraday":
        return (c / o - 1).fillna(0.0)
    return c.pct_change().fillna(0.0)


def simulate(close: pd.DataFrame, open_: pd.DataFrame, weights: pd.DataFrame, mode: str) -> tuple[pd.Series, float]:
    returns = return_matrix(close, open_, weights, mode)
    turnover = weights.diff().abs().sum(axis=1).fillna(0.0)
    daily = (weights.shift(1).fillna(0.0) * returns).sum(axis=1) - turnover * 10 / 10_000
    annual_turn = turnover.sum() / (len(weights) / TRADING_DAYS)
    return daily, annual_turn


def metrics(returns: pd.Series, turnover: float) -> dict[str, float]:
    r = returns.loc[START:].dropna()
    eq = (1 + r).cumprod()
    years = len(r) / TRADING_DAYS
    return {
        "cagr": eq.iloc[-1] ** (1 / years) - 1,
        "sharpe": r.mean() / r.std() * np.sqrt(TRADING_DAYS) if r.std() > 0 else np.nan,
        "max_drawdown": (eq / eq.cummax() - 1).min(),
        "worst_12m": eq.pct_change(TRADING_DAYS).min(),
        "turnover": turnover,
        "end_value": ACCOUNT_VALUE * eq.iloc[-1],
    }


def order_sheet(weights: pd.DataFrame, close: pd.DataFrame, strategy_id: str) -> pd.DataFrame:
    latest_weights = weights.iloc[-1]
    targets = latest_weights * ACCOUNT_VALUE
    latest_prices = close.loc[close.index.max()]
    rows = []
    for ticker in sorted(set(targets.index) | set(CURRENT_VALUES)):
        current = CURRENT_VALUES.get(ticker, 0.0)
        target = float(targets.get(ticker, 0.0))
        if abs(current) < 50 and abs(target) < 50:
            continue
        price = float(latest_prices[ticker]) if ticker in latest_prices.index and pd.notna(latest_prices[ticker]) else np.nan
        trade = target - current
        rows.append(
            {
                "strategy_id": strategy_id,
                "ticker": ticker,
                "current_value": current,
                "target_value": target,
                "trade_dollars": trade,
                "price": price,
                "approx_shares": trade / price if pd.notna(price) and price > 0 else np.nan,
            }
        )
    return pd.DataFrame(rows).sort_values("target_value", ascending=False)


def run_grid() -> tuple[pd.DataFrame, dict[str, pd.DataFrame], pd.DataFrame, pd.DataFrame]:
    close, open_, fundamentals = load_data()
    rows = []
    weight_cache: dict[str, pd.DataFrame] = {}
    for size_transform in [
        "equal",
        "quarter_cap_rank",
        "sqrt_cap_rank",
        "cap_rank",
        "sqrt_raw_cap",
        "raw_cap",
        "log_cap",
        "small_tilt",
        "sqrt_small_tilt",
        "barbell",
    ]:
        for size_power in [0.5, 1.0, 1.5]:
            for earn_transform in ["none", "sqrt", "linear", "square", "growth_only", "quality_growth"]:
                for earn_power in [0.5, 1.0, 1.5]:
                    for mom_power in [0.0, 0.5, 1.0, 1.5]:
                        for max_weight in [0.15, 0.20, 0.30]:
                            for cadence in ["weekly", "monthly"]:
                                weights = build_weights(
                                    close,
                                    fundamentals,
                                    size_transform,
                                    size_power,
                                    earn_transform,
                                    earn_power,
                                    mom_power,
                                    max_weight,
                                    cadence,
                                )
                                base_id = (
                                    f"size={size_transform}^{size_power}|earn={earn_transform}^{earn_power}|"
                                    f"mom={mom_power}|max={max_weight}|{cadence}"
                                )
                                for mode in ["close", "overnight", "intraday"]:
                                    daily, turn = simulate(close, open_, weights, mode)
                                    strategy_id = f"{base_id}|{mode}"
                                    rows.append(
                                        {
                                            "strategy_id": strategy_id,
                                            "size_transform": size_transform,
                                            "size_power": size_power,
                                            "earn_transform": earn_transform,
                                            "earn_power": earn_power,
                                            "momentum_power": mom_power,
                                            "max_name_weight": max_weight,
                                            "cadence": cadence,
                                            "return_mode": mode,
                                            **metrics(daily, turn),
                                        }
                                    )
                                    weight_cache[strategy_id] = weights
    return pd.DataFrame(rows), weight_cache, close, fundamentals


def write_outputs(results: pd.DataFrame, weights: dict[str, pd.DataFrame], close: pd.DataFrame, fundamentals: pd.DataFrame) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    results.to_csv(OUT / "transform_grid_results.csv", index=False)
    top = results.sort_values(["cagr", "sharpe"], ascending=False).head(50)
    top.to_markdown(OUT / "transform_grid_top50.md", index=False)

    close_only = results[results["return_mode"] == "close"]
    best_raw = results.sort_values(["cagr", "sharpe"], ascending=False).iloc[0]
    best_close = close_only.sort_values(["cagr", "sharpe"], ascending=False).iloc[0]
    robust_pool = close_only[
        (close_only["max_name_weight"] <= 0.20)
        & (close_only["turnover"] <= 20.0)
    ]
    best_robust = robust_pool.sort_values(["cagr", "sharpe"], ascending=False).iloc[0]
    best_overnight = results[results["return_mode"] == "overnight"].sort_values(["cagr", "sharpe"], ascending=False).iloc[0]
    best_intraday = results[results["return_mode"] == "intraday"].sort_values(["cagr", "sharpe"], ascending=False).iloc[0]

    selected_id = str(best_close["strategy_id"])
    selected_orders = order_sheet(weights[selected_id], close, selected_id)
    selected_orders.to_csv(OUT / "transform_grid_best_order_sheet.csv", index=False)
    selected_weights = weights[selected_id].iloc[-1].sort_values(ascending=False)
    selected_weights.to_csv(OUT / "transform_grid_best_weights.csv")

    fig, ax = plt.subplots(figsize=(12, 7), dpi=160)
    sample = results
    sc = ax.scatter(
        sample["max_drawdown"].abs() * 100,
        sample["cagr"] * 100,
        c=sample["sharpe"],
        cmap="viridis",
        s=10,
        alpha=0.55,
    )
    for label, row, color in [
        ("best close", best_close, "#ef4444"),
        ("best robust", best_robust, "#22c55e"),
        ("best overnight", best_overnight, "#3b82f6"),
    ]:
        ax.scatter(abs(row["max_drawdown"]) * 100, row["cagr"] * 100, color=color, s=170, edgecolor="white", linewidth=1.2)
        ax.annotate(label, (abs(row["max_drawdown"]) * 100, row["cagr"] * 100), xytext=(7, 7), textcoords="offset points")
    ax.set_title("Expanded Grid: Cap/Earnings/Momentum Transforms + Timing")
    ax.set_xlabel("10-year max drawdown, lower is better")
    ax.set_ylabel("10-year CAGR, higher is better")
    ax.grid(True, alpha=0.25)
    cbar = fig.colorbar(sc, ax=ax)
    cbar.set_label("Sharpe")
    chart = OUT / "transform_grid_chart.png"
    fig.savefig(chart, bbox_inches="tight")

    def fmt(row: pd.Series) -> str:
        return (
            f"`{row['strategy_id']}`: CAGR {row['cagr']*100:.1f}%, Sharpe {row['sharpe']:.2f}, "
            f"MaxDD {row['max_drawdown']*100:.1f}%, turnover {row['turnover']:.1f}x"
        )

    summary = [
        "# Expanded Transform Grid Search",
        "",
        "This grid explicitly tests market-cap smoothing and small-cap tilts.",
        "",
        "## What Was Tested",
        "- Size transforms: equal, cap rank, quarter/sqrt cap rank, log cap, sqrt/raw cap, small-cap tilt, sqrt small-cap tilt, barbell.",
        "- Earnings transforms: none, sqrt, linear, square, growth-only, quality-growth blend.",
        "- Momentum powers: 0.0, 0.5, 1.0, 1.5.",
        "- Max single AI name caps: 15%, 20%, 30% of the AI sleeve.",
        "- Rebalance: weekly/monthly.",
        "- Timing: close-to-close, overnight, intraday.",
        "",
        "## Winners",
        f"- Best raw across all timing modes: {fmt(best_raw)}",
        f"- Best close-to-close: {fmt(best_close)}",
        f"- Best robust close-to-close: {fmt(best_robust)}",
        f"- Best overnight: {fmt(best_overnight)}",
        f"- Best intraday: {fmt(best_intraday)}",
        "",
        "## Selected Best Close-To-Close Current Weights",
        selected_weights.to_frame("weight").to_markdown(),
        "",
        "## Selected Best Close-To-Close Order Sheet",
        selected_orders.to_markdown(index=False, floatfmt=".2f"),
        "",
        "## Notes",
        "- Best close-to-close is the highest total-return version.",
        "- Best overnight has cleaner Sharpe/lower drawdown but less total return.",
        "- Static current fundamentals create lookahead bias. Treat this as allocation research, not a point-in-time proof.",
        f"- Chart: `{chart.name}`",
    ]
    (OUT / "TRANSFORM_GRID_SEARCH.md").write_text("\n".join(summary) + "\n")


def main() -> None:
    results, weights, close, fundamentals = run_grid()
    write_outputs(results, weights, close, fundamentals)


if __name__ == "__main__":
    main()
