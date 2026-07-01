from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "work" / "cache"
OUT = ROOT / "outputs"
os.environ.setdefault("MPLCONFIGDIR", str(CACHE / "mpl"))

import matplotlib.pyplot as plt

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


def percentile_score(series: pd.Series, neutral: float = 0.55) -> pd.Series:
    return series.replace([np.inf, -np.inf], np.nan).rank(pct=True).fillna(neutral).clip(0.05, 1.0)


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    close = pd.read_csv(CACHE / "grid_prices.csv", parse_dates=["Date"], index_col="Date")
    open_ = pd.read_csv(CACHE / "grid_open_prices.csv", parse_dates=["Date"], index_col="Date")
    fundamentals = pd.read_csv(CACHE / "grid_fundamentals_raw.csv")
    f = fundamentals.copy()
    f["cap_score"] = percentile_score(np.log(f["market_cap"].clip(lower=1.0)))
    f["earnings_growth_score"] = percentile_score(f["earnings_quarterly_growth"].clip(-1.0, 3.0))
    f["revenue_growth_score"] = percentile_score(f["revenue_growth"].clip(-1.0, 2.0))
    f["margin_score"] = percentile_score(f["profit_margins"].clip(-1.0, 1.0))
    f["roe_score"] = percentile_score(f["return_on_equity"].clip(-2.0, 3.0))
    f["eps_score"] = percentile_score(f["forward_eps"].fillna(f["trailing_eps"]).clip(-100, 500))
    f["earnings_score"] = (
        0.35 * f["earnings_growth_score"]
        + 0.25 * f["revenue_growth_score"]
        + 0.20 * f["margin_score"]
        + 0.10 * f["roe_score"]
        + 0.10 * f["eps_score"]
    ).clip(0.05, 1.0)
    return close, open_, f.set_index("ticker")


def cap_row(row: pd.Series, max_weight: float) -> pd.Series:
    row = row.astype(float).clip(lower=0.0)
    if row.sum() <= 0:
        return row
    w = row / row.sum()
    active = w > 0
    cap = max(max_weight, 1.0 / active.sum())
    for _ in range(10):
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
    scores: pd.DataFrame,
    cap_exp: float,
    earnings_exp: float,
    momentum_exp: float,
    max_weight: float,
    cadence: str,
) -> pd.DataFrame:
    px = close[UNIVERSE].dropna(how="all")
    above = px > px.rolling(100).mean()
    valid = px.rolling(126).count().ge(126)
    basket_nav = (1 + px.pct_change().mean(axis=1).fillna(0)).cumprod()
    gate = basket_nav > basket_nav.rolling(100).mean()
    active = above & valid
    active = active.mul(gate, axis=0)

    cap_score = scores.reindex(UNIVERSE)["cap_score"].fillna(0.55) ** cap_exp
    earn_score = scores.reindex(UNIVERSE)["earnings_score"].fillna(0.55) ** earnings_exp
    static = cap_score * earn_score
    mom = (px / px.shift(126) - 1).rank(axis=1, pct=True).fillna(0.5).clip(0.05, 1.0) ** momentum_exp
    raw = active.astype(float).mul(static, axis=1) * mom
    raw = raw.where(raw.sum(axis=1) > 0, 0.0)

    rebal = rebalance_mask(raw.index, cadence)
    ai = pd.DataFrame(np.nan, index=raw.index, columns=UNIVERSE)
    capped = raw.loc[rebal].apply(lambda row: cap_row(row, max_weight), axis=1)
    ai.loc[rebal] = capped
    ai = ai.ffill().fillna(0.0)
    # When basket gate is off on a rebalance date, keep AI sleeve in BIL.
    ai = ai.mul(AI_SLEEVE, axis=0)
    weights = ai.copy()
    weights["QQQ"] = QQQ_WEIGHT
    weights["BIL"] = CASH_WEIGHT + (AI_SLEEVE - ai.sum(axis=1))
    return weights


def returns_for_mode(close: pd.DataFrame, open_: pd.DataFrame, weights: pd.DataFrame, mode: str) -> pd.DataFrame:
    c = close.reindex(weights.index)[weights.columns]
    o = open_.reindex(weights.index)[weights.columns]
    if mode == "overnight":
        return (o / c.shift(1) - 1).fillna(0.0)
    if mode == "intraday":
        return (c / o - 1).fillna(0.0)
    return c.pct_change().fillna(0.0)


def simulate(close: pd.DataFrame, open_: pd.DataFrame, weights: pd.DataFrame, mode: str) -> tuple[pd.Series, float]:
    r = returns_for_mode(close, open_, weights, mode)
    turnover = weights.diff().abs().sum(axis=1).fillna(0.0)
    daily = (weights.shift(1).fillna(0.0) * r).sum(axis=1) - turnover * 10 / 10_000
    ann_turn = turnover.sum() / (len(weights) / TRADING_DAYS)
    return daily, ann_turn


def metrics(r: pd.Series, turnover: float) -> dict[str, float]:
    r = r.loc[START:].dropna()
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


def run() -> tuple[pd.DataFrame, dict[str, pd.DataFrame], pd.DataFrame, pd.DataFrame]:
    close, open_, scores = load_data()
    models = [
        ("equal", 0, 0, 0),
        ("sqrt_cap", 0.5, 0, 0),
        ("market_cap", 1, 0, 0),
        ("earnings", 0, 1, 0),
        ("momentum", 0, 0, 1),
        ("cap_earnings", 0.5, 1, 0),
        ("earnings_momentum", 0, 1, 1),
        ("cap_earnings_momentum", 0.5, 1, 1),
        ("mega_cap_earnings_momentum", 1, 0.5, 1),
    ]
    rows = []
    weight_cache = {}
    for name, cap_exp, earn_exp, mom_exp in models:
        for max_w in [0.15, 0.20, 0.30]:
            for cadence in ["weekly", "monthly"]:
                weights = build_weights(close, scores, cap_exp, earn_exp, mom_exp, max_w, cadence)
                base_id = f"{name}_max{max_w}_{cadence}"
                for mode in ["close", "overnight", "intraday"]:
                    r, turn = simulate(close, open_, weights, mode)
                    sid = f"{base_id}_{mode}"
                    rows.append(
                        {
                            "strategy_id": sid,
                            "model": name,
                            "max_name_weight": max_w,
                            "cadence": cadence,
                            "return_mode": mode,
                            **metrics(r, turn),
                        }
                    )
                    weight_cache[sid] = weights
    return pd.DataFrame(rows), weight_cache, close, scores


def order_sheet(weights: pd.DataFrame, close: pd.DataFrame, strategy_id: str) -> pd.DataFrame:
    latest = weights.iloc[-1] * ACCOUNT_VALUE
    prices = close.loc[close.index.max()]
    rows = []
    for ticker in sorted(set(latest.index) | set(CURRENT_VALUES)):
        current = CURRENT_VALUES.get(ticker, 0.0)
        target = float(latest.get(ticker, 0.0))
        if abs(target) < 50 and abs(current) < 50:
            continue
        trade = target - current
        price = float(prices[ticker]) if ticker in prices.index and pd.notna(prices[ticker]) else np.nan
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


def write_outputs(results: pd.DataFrame, weights: dict[str, pd.DataFrame], close: pd.DataFrame, scores: pd.DataFrame) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    results.to_csv(OUT / "fast_grid_weight_timing_results.csv", index=False)
    top = results.sort_values(["cagr", "sharpe"], ascending=False).head(25)
    top.to_markdown(OUT / "fast_grid_top25.md", index=False)

    best_cagr = results.sort_values(["cagr", "sharpe"], ascending=False).iloc[0]
    best_sharpe = results.sort_values(["sharpe", "cagr"], ascending=False).iloc[0]
    close_only = results[results["return_mode"] == "close"]
    best_close = close_only.sort_values(["cagr", "sharpe"], ascending=False).iloc[0]
    robust_pool = close_only[(close_only["max_name_weight"] <= 0.20) & (close_only["turnover"] <= 20)]
    best_robust = robust_pool.sort_values(["cagr", "sharpe"], ascending=False).iloc[0]
    best_overnight = results[results["return_mode"] == "overnight"].sort_values(["cagr", "sharpe"], ascending=False).iloc[0]
    best_intraday = results[results["return_mode"] == "intraday"].sort_values(["cagr", "sharpe"], ascending=False).iloc[0]

    selected_id = str(best_robust["strategy_id"])
    orders = order_sheet(weights[selected_id], close, selected_id)
    orders.to_csv(OUT / "fast_grid_selected_order_sheet.csv", index=False)
    selected_weights = weights[selected_id].iloc[-1].sort_values(ascending=False)
    selected_weights.to_csv(OUT / "fast_grid_selected_weights.csv")

    fig, ax = plt.subplots(figsize=(11, 7), dpi=160)
    sc = ax.scatter(
        results["max_drawdown"].abs() * 100,
        results["cagr"] * 100,
        c=results["sharpe"],
        cmap="viridis",
        s=38,
        alpha=0.75,
    )
    for label, row, color in [
        ("best raw", best_cagr, "#ef4444"),
        ("best close", best_close, "#f97316"),
        ("best robust", best_robust, "#22c55e"),
        ("best overnight", best_overnight, "#3b82f6"),
    ]:
        ax.scatter(abs(row["max_drawdown"]) * 100, row["cagr"] * 100, color=color, s=170, edgecolor="white", linewidth=1.2)
        ax.annotate(label, (abs(row["max_drawdown"]) * 100, row["cagr"] * 100), xytext=(6, 6), textcoords="offset points")
    ax.set_title("Fast Grid: Weighting + Timing")
    ax.set_xlabel("10-year max drawdown, lower is better")
    ax.set_ylabel("10-year CAGR, higher is better")
    ax.grid(True, alpha=0.25)
    cbar = fig.colorbar(sc, ax=ax)
    cbar.set_label("Sharpe")
    chart = OUT / "fast_grid_weight_timing_chart.png"
    fig.savefig(chart, bbox_inches="tight")

    def fmt(row: pd.Series) -> str:
        return (
            f"`{row['strategy_id']}`: CAGR {row['cagr']*100:.1f}%, Sharpe {row['sharpe']:.2f}, "
            f"MaxDD {row['max_drawdown']*100:.1f}%, turnover {row['turnover']:.1f}x"
        )

    report = [
        "# Fast Grid Search - Weighting And Timing",
        "",
        "Universe includes AVGO and INTC. Data source for full universe: Yahoo Finance via yfinance cache.",
        "",
        "## Caveats",
        "- Current market cap and earnings scores are static current fundamentals, not point-in-time history.",
        "- Overnight/intraday tests use daily Open/Close, not minute-level data.",
        "- Newer names have shorter histories, so every AI basket result still has survivorship/listing bias.",
        "",
        "## Winners",
        f"- Best raw CAGR across all timing modes: {fmt(best_cagr)}",
        f"- Best Sharpe across all timing modes: {fmt(best_sharpe)}",
        f"- Best close-to-close raw CAGR: {fmt(best_close)}",
        f"- Best overnight-only: {fmt(best_overnight)}",
        f"- Best intraday-only: {fmt(best_intraday)}",
        f"- Best robust pick I would use: {fmt(best_robust)}",
        "",
        "## Plain-English Pick",
        "Use the best robust close-to-close strategy: cap+earnings+momentum weighting, weekly or monthly depending on the selected row below. It keeps the AI sleeve aggressive but does not let one name dominate.",
        "",
        "## Selected Current Weights",
        selected_weights.to_frame("weight").to_markdown(),
        "",
        "## Selected Order Sheet",
        orders.to_markdown(index=False, floatfmt=".2f"),
        "",
        "## Fundamental Scores Used",
        scores[["market_cap", "earnings_quarterly_growth", "revenue_growth", "profit_margins", "return_on_equity", "cap_score", "earnings_score"]]
        .sort_values("earnings_score", ascending=False)
        .to_markdown(),
        "",
        f"Chart: `{chart.name}`",
    ]
    (OUT / "FAST_GRID_WEIGHT_TIMING.md").write_text("\n".join(report) + "\n")


def main() -> None:
    results, weights, close, scores = run()
    write_outputs(results, weights, close, scores)


if __name__ == "__main__":
    main()
