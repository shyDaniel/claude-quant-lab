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

UNIVERSE = ["NVDA", "AMD", "AVGO", "INTC", "MU", "SNDK", "MRVL", "STX", "ANET", "VST", "CEG", "GEV", "VRT", "NBIS", "SMCI"]
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


def pct(series: pd.Series) -> pd.Series:
    return series.replace([np.inf, -np.inf], np.nan).rank(pct=True).fillna(0.55).clip(0.05, 1.0)


def load() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    close = pd.read_csv(CACHE / "grid_prices.csv", parse_dates=["Date"], index_col="Date")
    open_ = pd.read_csv(CACHE / "grid_open_prices.csv", parse_dates=["Date"], index_col="Date")
    f = pd.read_csv(CACHE / "grid_fundamentals_raw.csv").set_index("ticker")
    f["cap_rank"] = pct(np.log(f["market_cap"].clip(lower=1)))
    f["earn_growth"] = pct(f["earnings_quarterly_growth"].clip(-1, 3))
    f["rev_growth"] = pct(f["revenue_growth"].clip(-1, 2))
    f["margin"] = pct(f["profit_margins"].clip(-1, 1))
    f["roe"] = pct(f["return_on_equity"].clip(-2, 3))
    f["eps"] = pct(f["forward_eps"].fillna(f["trailing_eps"]).clip(-100, 500))
    f["earn_score"] = (0.35 * f["earn_growth"] + 0.25 * f["rev_growth"] + 0.2 * f["margin"] + 0.1 * f["roe"] + 0.1 * f["eps"]).clip(0.05, 1)
    return close, open_, f


def size_vector(f: pd.DataFrame, transform: str) -> pd.Series:
    cap = f.reindex(UNIVERSE)["market_cap"].clip(lower=1)
    rank = f.reindex(UNIVERSE)["cap_rank"].fillna(0.55)
    if transform == "equal":
        return pd.Series(1.0, index=UNIVERSE)
    if transform == "sqrt_cap_rank":
        return rank ** 0.5
    if transform == "cap_rank":
        return rank
    if transform == "log_cap":
        return np.log(cap) / np.log(cap).median()
    if transform == "sqrt_raw_cap":
        return (cap / cap.median()) ** 0.5
    if transform == "small_tilt":
        return (1.05 - rank).clip(0.05, 1)
    if transform == "barbell":
        return (rank - 0.5).abs() * 2 + 0.1
    raise ValueError(transform)


def earn_vector(f: pd.DataFrame, transform: str) -> pd.Series:
    e = f.reindex(UNIVERSE)["earn_score"].fillna(0.55).clip(0.05, 1)
    if transform == "none":
        return pd.Series(1.0, index=UNIVERSE)
    if transform == "sqrt":
        return e ** 0.5
    if transform == "linear":
        return e
    if transform == "square":
        return e ** 2
    if transform == "growth_only":
        return f.reindex(UNIVERSE)["earn_growth"].fillna(0.55).clip(0.05, 1)
    raise ValueError(transform)


def rebalance_mask(index: pd.DatetimeIndex, cadence: str) -> pd.Series:
    if cadence == "weekly":
        return index.to_series().groupby([index.isocalendar().year, index.isocalendar().week]).transform("max") == index
    return index.to_series().groupby(index.to_period("M")).transform("max") == index


def normalize_top(row: pd.Series, top_n: int) -> pd.Series:
    out = pd.Series(0.0, index=row.index)
    pos = row[row > 0].sort_values(ascending=False).head(top_n)
    if pos.sum() > 0:
        out.loc[pos.index] = pos / pos.sum()
    return out


def weights(close: pd.DataFrame, f: pd.DataFrame, size_t: str, earn_t: str, mom_power: float, top_n: int, cadence: str) -> pd.DataFrame:
    px = close[UNIVERSE].dropna(how="all")
    active = (px > px.rolling(100).mean()) & px.rolling(126).count().ge(126)
    basket = (1 + px.pct_change().mean(axis=1).fillna(0)).cumprod()
    active = active.mul(basket > basket.rolling(100).mean(), axis=0)
    mom = (px / px.shift(126) - 1).rank(axis=1, pct=True).fillna(0.5).clip(0.05, 1) ** mom_power
    static = size_vector(f, size_t) * earn_vector(f, earn_t)
    raw = active.astype(float).mul(static, axis=1) * mom
    rebal = rebalance_mask(raw.index, cadence)
    ai = pd.DataFrame(np.nan, index=raw.index, columns=UNIVERSE)
    ai.loc[rebal] = raw.loc[rebal].apply(lambda r: normalize_top(r, top_n), axis=1)
    ai = ai.ffill().fillna(0) * AI_SLEEVE
    w = ai.copy()
    w["QQQ"] = QQQ_WEIGHT
    w["BIL"] = CASH_WEIGHT + (AI_SLEEVE - ai.sum(axis=1))
    return w


def sim(close: pd.DataFrame, open_: pd.DataFrame, w: pd.DataFrame, mode: str) -> tuple[pd.Series, float]:
    c = close.reindex(w.index)[w.columns]
    o = open_.reindex(w.index)[w.columns]
    if mode == "overnight":
        r = (o / c.shift(1) - 1).fillna(0)
    elif mode == "intraday":
        r = (c / o - 1).fillna(0)
    else:
        r = c.pct_change().fillna(0)
    turn = w.diff().abs().sum(axis=1).fillna(0)
    daily = (w.shift(1).fillna(0) * r).sum(axis=1) - turn * 10 / 10000
    return daily, turn.sum() / (len(w) / TRADING_DAYS)


def metrics(r: pd.Series, turn: float) -> dict[str, float]:
    r = r.loc[START:].dropna()
    eq = (1 + r).cumprod()
    years = len(r) / TRADING_DAYS
    return {
        "cagr": eq.iloc[-1] ** (1 / years) - 1,
        "sharpe": r.mean() / r.std() * np.sqrt(TRADING_DAYS) if r.std() > 0 else np.nan,
        "max_drawdown": (eq / eq.cummax() - 1).min(),
        "worst_12m": eq.pct_change(TRADING_DAYS).min(),
        "turnover": turn,
        "end_value": ACCOUNT_VALUE * eq.iloc[-1],
    }


def orders(w: pd.DataFrame, close: pd.DataFrame, sid: str) -> pd.DataFrame:
    latest = w.iloc[-1] * ACCOUNT_VALUE
    prices = close.loc[close.index.max()]
    rows = []
    for t in sorted(set(latest.index) | set(CURRENT_VALUES)):
        cur = CURRENT_VALUES.get(t, 0.0)
        target = float(latest.get(t, 0.0))
        if abs(cur) < 50 and abs(target) < 50:
            continue
        price = float(prices[t]) if t in prices.index and pd.notna(prices[t]) else np.nan
        trade = target - cur
        rows.append({"strategy_id": sid, "ticker": t, "current_value": cur, "target_value": target, "trade_dollars": trade, "price": price, "approx_shares": trade / price if pd.notna(price) and price > 0 else np.nan})
    return pd.DataFrame(rows).sort_values("target_value", ascending=False)


def main() -> None:
    close, open_, f = load()
    rows = []
    cache = {}
    for size_t in ["equal", "sqrt_cap_rank", "cap_rank", "log_cap", "sqrt_raw_cap", "small_tilt", "barbell"]:
        for earn_t in ["none", "sqrt", "linear", "square", "growth_only"]:
            for mom_power in [0.0, 0.5, 1.0, 1.5]:
                for top_n in [5, 7, 10, 12]:
                    for cadence in ["weekly", "monthly"]:
                        w = weights(close, f, size_t, earn_t, mom_power, top_n, cadence)
                        base = f"size={size_t}|earn={earn_t}|mom={mom_power}|top={top_n}|{cadence}"
                        for mode in ["close", "overnight", "intraday"]:
                            r, turn = sim(close, open_, w, mode)
                            sid = f"{base}|{mode}"
                            rows.append({"strategy_id": sid, "size_transform": size_t, "earn_transform": earn_t, "momentum_power": mom_power, "top_n": top_n, "cadence": cadence, "return_mode": mode, **metrics(r, turn)})
                            cache[sid] = w
    res = pd.DataFrame(rows)
    OUT.mkdir(exist_ok=True)
    res.to_csv(OUT / "medium_transform_grid_results.csv", index=False)
    res.sort_values(["cagr", "sharpe"], ascending=False).head(50).to_markdown(OUT / "medium_transform_grid_top50.md", index=False)
    close_res = res[res.return_mode == "close"]
    best_close = close_res.sort_values(["cagr", "sharpe"], ascending=False).iloc[0]
    best_robust = close_res[(close_res.top_n >= 7) & (close_res.turnover <= 20)].sort_values(["cagr", "sharpe"], ascending=False).iloc[0]
    best_overnight = res[res.return_mode == "overnight"].sort_values(["cagr", "sharpe"], ascending=False).iloc[0]
    selected = best_close
    sid = str(selected.strategy_id)
    order = orders(cache[sid], close, sid)
    order.to_csv(OUT / "medium_transform_best_order_sheet.csv", index=False)
    cache[sid].iloc[-1].sort_values(ascending=False).to_csv(OUT / "medium_transform_best_weights.csv")
    fig, ax = plt.subplots(figsize=(12, 7), dpi=160)
    sc = ax.scatter(res.max_drawdown.abs() * 100, res.cagr * 100, c=res.sharpe, s=13, alpha=0.55, cmap="viridis")
    for label, row, color in [("best close", best_close, "#ef4444"), ("best robust", best_robust, "#22c55e"), ("best overnight", best_overnight, "#3b82f6")]:
        ax.scatter(abs(row.max_drawdown) * 100, row.cagr * 100, s=170, color=color, edgecolor="white")
        ax.annotate(label, (abs(row.max_drawdown) * 100, row.cagr * 100), xytext=(7, 7), textcoords="offset points")
    ax.set_title("Medium Grid: Size/Earnings Transforms + Timing")
    ax.set_xlabel("10-year max drawdown")
    ax.set_ylabel("10-year CAGR")
    ax.grid(True, alpha=0.25)
    fig.colorbar(sc, ax=ax, label="Sharpe")
    chart = OUT / "medium_transform_grid_chart.png"
    fig.savefig(chart, bbox_inches="tight")
    def fmt(row: pd.Series) -> str:
        return f"`{row.strategy_id}`: CAGR {row.cagr*100:.1f}%, Sharpe {row.sharpe:.2f}, MaxDD {row.max_drawdown*100:.1f}%, turnover {row.turnover:.1f}x"
    report = [
        "# Medium Transform Grid Search",
        "",
        "This is the expanded but fast grid for cap smoothing/small-cap tilt and earnings transforms.",
        "",
        "## Winners",
        f"- Best close-to-close: {fmt(best_close)}",
        f"- Best robust close-to-close: {fmt(best_robust)}",
        f"- Best overnight: {fmt(best_overnight)}",
        "",
        "## Selected Best Weights",
        cache[sid].iloc[-1].sort_values(ascending=False).to_frame("weight").to_markdown(),
        "",
        "## Selected Order Sheet",
        order.to_markdown(index=False, floatfmt=".2f"),
        "",
        f"Chart: `{chart.name}`",
    ]
    (OUT / "MEDIUM_TRANSFORM_GRID_SEARCH.md").write_text("\n".join(report) + "\n")


if __name__ == "__main__":
    main()
