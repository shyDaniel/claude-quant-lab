from __future__ import annotations

import os
from dataclasses import dataclass
from itertools import product
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yfinance as yf


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
CACHE = ROOT / "work" / "cache"
os.environ.setdefault("MPLCONFIGDIR", str(CACHE / "mpl"))

START = "2015-01-01"
GRID_START = "2016-07-01"
END_LABEL = "2026-07-01"
TRADING_DAYS = 252
ACCOUNT_VALUE = 278_726.16
AI_SLEEVE = 0.70
QQQ_WEIGHT = 0.25
BASE_CASH = 0.05

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
TICKERS = sorted(set(["QQQ", "BIL"] + UNIVERSE))

CURRENT_VALUES = {
    "QQQ": 100.00 * 728.39,
    "NBIS": 120.00 * 234.92,
    "MU": 25.00 * 1063.06,
    "DRAM": 300.01 * 67.02,
    "NVDA": 100.01 * 199.53,
    "SMCI": 300.00 * 28.16,
    "CASH": 102_555.39,
}


@dataclass(frozen=True)
class GridParams:
    cap_exp: float
    earnings_exp: float
    momentum_exp: float
    max_name_weight: float
    rebalance: str
    return_mode: str


def download_prices() -> tuple[pd.DataFrame, pd.DataFrame]:
    CACHE.mkdir(parents=True, exist_ok=True)
    close_path = CACHE / "grid_prices.csv"
    open_path = CACHE / "grid_open_prices.csv"
    if close_path.exists() and open_path.exists():
        close = pd.read_csv(close_path, parse_dates=["Date"], index_col="Date")
        open_ = pd.read_csv(open_path, parse_dates=["Date"], index_col="Date")
        return close, open_
    raw = yf.download(TICKERS, start=START, auto_adjust=True, progress=False, threads=False)
    close = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw
    open_ = raw["Open"] if isinstance(raw.columns, pd.MultiIndex) else raw
    close = close.dropna(how="all").sort_index()
    open_ = open_.dropna(how="all").sort_index()
    close.index.name = "Date"
    open_.index.name = "Date"
    close.to_csv(CACHE / "grid_prices.csv")
    open_.to_csv(CACHE / "grid_open_prices.csv")
    return close, open_


def fetch_fundamentals() -> pd.DataFrame:
    path = CACHE / "grid_fundamentals_raw.csv"
    if path.exists():
        return pd.read_csv(path)
    rows = []
    for ticker in UNIVERSE:
        info = {}
        try:
            info = yf.Ticker(ticker).info
        except Exception as exc:
            print(f"fundamental fetch failed {ticker}: {exc}")
        rows.append(
            {
                "ticker": ticker,
                "market_cap": info.get("marketCap", np.nan),
                "earnings_quarterly_growth": info.get("earningsQuarterlyGrowth", np.nan),
                "revenue_growth": info.get("revenueGrowth", np.nan),
                "profit_margins": info.get("profitMargins", np.nan),
                "return_on_equity": info.get("returnOnEquity", np.nan),
                "forward_eps": info.get("forwardEps", np.nan),
                "trailing_eps": info.get("trailingEps", np.nan),
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)
    return df


def percentile_score(series: pd.Series, neutral: float = 0.55) -> pd.Series:
    clean = series.replace([np.inf, -np.inf], np.nan)
    ranks = clean.rank(pct=True)
    return ranks.fillna(neutral).clip(0.05, 1.0)


def build_static_scores(fundamentals: pd.DataFrame) -> pd.DataFrame:
    df = fundamentals.copy()
    df["cap_score"] = percentile_score(np.log(df["market_cap"].clip(lower=1.0)))
    df["earnings_growth_score"] = percentile_score(df["earnings_quarterly_growth"].clip(-1.0, 3.0))
    df["revenue_growth_score"] = percentile_score(df["revenue_growth"].clip(-1.0, 2.0))
    df["margin_score"] = percentile_score(df["profit_margins"].clip(-1.0, 1.0))
    df["roe_score"] = percentile_score(df["return_on_equity"].clip(-2.0, 3.0))
    df["eps_score"] = percentile_score(df["forward_eps"].fillna(df["trailing_eps"]).clip(-100.0, 500.0))
    df["earnings_score"] = (
        0.35 * df["earnings_growth_score"]
        + 0.25 * df["revenue_growth_score"]
        + 0.20 * df["margin_score"]
        + 0.10 * df["roe_score"]
        + 0.10 * df["eps_score"]
    ).clip(0.05, 1.0)
    df.to_csv(OUT / "grid_fundamental_scores.csv", index=False)
    return df.set_index("ticker")


def rebalance_mask(index: pd.DatetimeIndex, kind: str) -> pd.Series:
    if kind == "daily":
        return pd.Series(True, index=index)
    if kind == "weekly":
        return index.to_series().groupby([index.isocalendar().year, index.isocalendar().week]).transform("max") == index
    return index.to_series().groupby(index.to_period("M")).transform("max") == index


def cap_and_redistribute(weights: pd.Series, max_weight: float) -> pd.Series:
    weights = weights.astype(float).clip(lower=0.0)
    total = weights.sum()
    if total <= 0:
        return weights
    weights = weights / total
    active = weights > 0
    effective_cap = max(max_weight, 1.0 / active.sum())
    for _ in range(20):
        over = weights > effective_cap
        if not over.any():
            break
        over_idx = over[over].index
        excess = (weights.loc[over_idx] - effective_cap).sum()
        weights.loc[over_idx] = effective_cap
        under = active & ~over
        if not under.any() or excess <= 0:
            break
        under_idx = under[under].index
        weights.loc[under_idx] += excess * weights.loc[under_idx] / weights.loc[under_idx].sum()
    return weights / weights.sum()


def strategy_weights(prices: pd.DataFrame, scores: pd.DataFrame, params: GridParams) -> pd.DataFrame:
    px = prices[UNIVERSE].dropna(how="all")
    above_100d = px > px.rolling(100).mean()
    valid = px.rolling(126).count().ge(126)
    basket_nav = (1.0 + px.pct_change().mean(axis=1).fillna(0.0)).cumprod()
    basket_on = basket_nav > basket_nav.rolling(100).mean()
    mom = (px / px.shift(126) - 1.0).rank(axis=1, pct=True).fillna(0.5).clip(0.05, 1.0)
    cap_score = scores.reindex(UNIVERSE)["cap_score"].fillna(0.55)
    earnings_score = scores.reindex(UNIVERSE)["earnings_score"].fillna(0.55)
    base = (cap_score ** params.cap_exp) * (earnings_score ** params.earnings_exp)

    weights = pd.DataFrame(0.0, index=px.index, columns=UNIVERSE + ["QQQ", "BIL"])
    mask = rebalance_mask(px.index, params.rebalance)
    last_ai = pd.Series(0.0, index=UNIVERSE)
    for date in px.index:
        if bool(mask.loc[date]):
            active = above_100d.loc[date] & valid.loc[date] & bool(basket_on.loc[date])
            raw = pd.Series(0.0, index=UNIVERSE)
            if active.any():
                raw.loc[active.index[active]] = base.loc[active.index[active]] * (
                    mom.loc[date, active.index[active]] ** params.momentum_exp
                )
                last_ai = cap_and_redistribute(raw, params.max_name_weight)
            else:
                last_ai = pd.Series(0.0, index=UNIVERSE)
        weights.loc[date, UNIVERSE] = last_ai * AI_SLEEVE
        unused_ai = AI_SLEEVE - weights.loc[date, UNIVERSE].sum()
        weights.loc[date, "QQQ"] = QQQ_WEIGHT
        weights.loc[date, "BIL"] = BASE_CASH + unused_ai
    return weights


def return_matrix(close: pd.DataFrame, open_: pd.DataFrame, weights: pd.DataFrame, mode: str) -> pd.DataFrame:
    close_sub = close.reindex(weights.index)[weights.columns]
    open_sub = open_.reindex(weights.index)[weights.columns]
    if mode == "overnight_only":
        return (open_sub / close_sub.shift(1) - 1.0).fillna(0.0)
    if mode == "intraday_only":
        return (close_sub / open_sub - 1.0).fillna(0.0)
    return close_sub.pct_change().fillna(0.0)


def simulate(
    close: pd.DataFrame,
    open_: pd.DataFrame,
    weights: pd.DataFrame,
    mode: str,
    cost_bps: float = 10.0,
) -> tuple[pd.Series, float]:
    returns = return_matrix(close, open_, weights, mode)
    gross = (weights.shift(1).fillna(0.0) * returns).sum(axis=1)
    turnover = weights.diff().abs().sum(axis=1).fillna(0.0)
    net = gross - turnover * cost_bps / 10_000.0
    annual_turnover = turnover.sum() / (len(weights) / TRADING_DAYS)
    return net, annual_turnover


def metrics(returns: pd.Series, turnover: float, start: str = GRID_START) -> dict[str, float]:
    r = returns.loc[start:].dropna()
    equity = (1.0 + r).cumprod()
    years = len(r) / TRADING_DAYS
    return {
        "cagr": equity.iloc[-1] ** (1.0 / years) - 1.0,
        "sharpe": r.mean() / r.std() * np.sqrt(TRADING_DAYS) if r.std() > 0 else np.nan,
        "max_drawdown": (equity / equity.cummax() - 1.0).min(),
        "worst_12m": equity.pct_change(TRADING_DAYS).min(),
        "volatility": r.std() * np.sqrt(TRADING_DAYS),
        "turnover": turnover,
        "end_value": ACCOUNT_VALUE * equity.iloc[-1],
    }


def run_grid(close: pd.DataFrame, open_: pd.DataFrame, scores: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    param_rows = []
    weight_cache: dict[str, pd.DataFrame] = {}
    grid = product(
        [0.0, 0.5, 1.0],
        [0.0, 1.0],
        [0.0, 1.0],
        [0.15, 0.20, 0.30],
        ["weekly", "monthly"],
        ["close_to_close", "overnight_only", "intraday_only"],
    )
    for cap_exp, earn_exp, mom_exp, max_w, rebalance, return_mode in grid:
        params = GridParams(cap_exp, earn_exp, mom_exp, max_w, rebalance, return_mode)
        weights = strategy_weights(close, scores, params)
        returns, turnover = simulate(close, open_, weights, return_mode)
        row = {
            "strategy_id": f"cap{cap_exp}_earn{earn_exp}_mom{mom_exp}_max{max_w}_{rebalance}_{return_mode}",
            "cap_exp": cap_exp,
            "earnings_exp": earn_exp,
            "momentum_exp": mom_exp,
            "max_name_weight": max_w,
            "rebalance": rebalance,
            "return_mode": return_mode,
            **metrics(returns, turnover),
        }
        param_rows.append(row)
        weight_cache[row["strategy_id"]] = weights
    results = pd.DataFrame(param_rows)
    results.to_csv(OUT / "grid_search_marketcap_earnings.csv", index=False)
    return results, weight_cache


def target_orders(weights: pd.DataFrame, prices: pd.DataFrame, strategy_id: str) -> pd.DataFrame:
    latest_weights = weights.iloc[-1].copy()
    targets = latest_weights * ACCOUNT_VALUE
    tickers = [ticker for ticker in latest_weights.index if targets[ticker] > 100 or ticker in CURRENT_VALUES]
    latest_prices = prices.loc[prices.index.max()]
    rows = []
    for ticker in sorted(set(tickers) | set(CURRENT_VALUES)):
        current = CURRENT_VALUES.get(ticker, 0.0)
        target = float(targets.get(ticker, 0.0))
        trade = target - current
        price = float(latest_prices[ticker]) if ticker in latest_prices.index and pd.notna(latest_prices[ticker]) else np.nan
        shares = trade / price if pd.notna(price) and price > 0 else np.nan
        rows.append(
            {
                "strategy_id": strategy_id,
                "ticker": ticker,
                "price": price,
                "current_value": current,
                "target_value": target,
                "trade_dollars": trade,
                "approx_shares": shares,
            }
        )
    return pd.DataFrame(rows).sort_values("target_value", ascending=False)


def write_report(results: pd.DataFrame, weights: dict[str, pd.DataFrame], prices: pd.DataFrame, scores: pd.DataFrame) -> None:
    best_cagr = results.sort_values(["cagr", "sharpe"], ascending=False).iloc[0]
    best_sharpe = results.sort_values(["sharpe", "cagr"], ascending=False).iloc[0]
    robust_pool = results[
        (results["max_name_weight"] <= 0.20)
        & (results["turnover"] <= 20.0)
        & (results["return_mode"] == "close_to_close")
    ]
    best_robust = robust_pool.sort_values(["cagr", "sharpe"], ascending=False).iloc[0]
    best_overnight = results[results["return_mode"] == "overnight_only"].sort_values(["cagr", "sharpe"], ascending=False).iloc[0]
    best_intraday = results[results["return_mode"] == "intraday_only"].sort_values(["cagr", "sharpe"], ascending=False).iloc[0]

    orders = target_orders(weights[best_robust["strategy_id"]], prices, str(best_robust["strategy_id"]))
    orders.to_csv(OUT / "grid_best_robust_order_sheet.csv", index=False)
    weights[best_robust["strategy_id"]].tail(1).T.rename(columns={weights[best_robust["strategy_id"]].index[-1]: "weight"}).to_csv(
        OUT / "grid_best_robust_weights.csv"
    )

    top = results.sort_values("cagr", ascending=False).head(15)
    top.to_markdown(OUT / "grid_search_top15.md", index=False)

    fig, ax = plt.subplots(figsize=(11, 7), dpi=160)
    sc = ax.scatter(
        results["max_drawdown"].abs() * 100,
        results["cagr"] * 100,
        c=results["sharpe"],
        cmap="viridis",
        s=45,
        alpha=0.75,
    )
    for label, row, color in [
        ("best CAGR", best_cagr, "#ef4444"),
        ("best robust", best_robust, "#22c55e"),
        ("best Sharpe", best_sharpe, "#3b82f6"),
    ]:
        ax.scatter(abs(row["max_drawdown"]) * 100, row["cagr"] * 100, s=180, color=color, edgecolor="white", linewidth=1.5)
        ax.annotate(label, (abs(row["max_drawdown"]) * 100, row["cagr"] * 100), xytext=(7, 7), textcoords="offset points")
    ax.set_title("Grid Search: Market-Cap + Earnings + Momentum Weighting")
    ax.set_xlabel("10-year max drawdown, lower is better")
    ax.set_ylabel("10-year CAGR, higher is better")
    ax.grid(True, alpha=0.25)
    cbar = fig.colorbar(sc, ax=ax)
    cbar.set_label("Sharpe")
    fig.text(0.02, 0.02, "Uses current fundamentals as static scores, so this is allocation research, not clean point-in-time proof.", fontsize=9)
    chart = OUT / "grid_search_marketcap_earnings_chart.png"
    fig.savefig(chart, bbox_inches="tight")

    def fmt_row(row: pd.Series) -> str:
        return (
            f"`{row['strategy_id']}`: CAGR {row['cagr']*100:.1f}%, Sharpe {row['sharpe']:.2f}, "
            f"MaxDD {row['max_drawdown']*100:.1f}%, turnover {row['turnover']:.1f}x"
        )

    report = [
        "# Market-Cap + Earnings Grid Search",
        "",
        f"Window: {GRID_START} through {prices.index.max().date()}",
        "Universe includes AVGO and INTC.",
        "",
        "## Important Caveat",
        "Market cap and earnings scores are current yfinance fundamentals, not point-in-time historical",
        "fundamentals. That means this grid search has lookahead bias. Use it to choose today's weighting",
        "scheme, not as proof that the exact weighting would have been knowable 10 years ago.",
        "",
        "## Winners",
        f"- Best raw 10-year CAGR: {fmt_row(best_cagr)}",
        f"- Best 10-year Sharpe: {fmt_row(best_sharpe)}",
        f"- Best overnight-only: {fmt_row(best_overnight)}",
        f"- Best intraday-only: {fmt_row(best_intraday)}",
        f"- Best robust pick I would actually use: {fmt_row(best_robust)}",
        "",
        "Robust pick constraint: close-to-close, max single AI name <= 20% of the AI sleeve, and annual turnover <= 20x.",
        "Overnight/intraday rows use daily Open/Close decomposition; this is not minute-level timing.",
        "",
        "## Best Robust Current Weights",
        weights[best_robust["strategy_id"]].tail(1).T.rename(columns={weights[best_robust["strategy_id"]].index[-1]: "weight"}).sort_values(
            "weight", ascending=False
        ).to_markdown(),
        "",
        "## Best Robust Order Sheet",
        orders.to_markdown(index=False, floatfmt=".2f"),
        "",
        "## Fundamentals Used",
        scores.reset_index()[
            [
                "ticker",
                "market_cap",
                "earnings_quarterly_growth",
                "revenue_growth",
                "profit_margins",
                "return_on_equity",
                "cap_score",
                "earnings_score",
            ]
        ].sort_values("earnings_score", ascending=False).to_markdown(index=False),
        "",
        f"Chart: `{chart.name}`",
    ]
    (OUT / "GRID_SEARCH_MARKETCAP_EARNINGS.md").write_text("\n".join(report) + "\n")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    prices, open_prices = download_prices()
    fundamentals = fetch_fundamentals()
    scores = build_static_scores(fundamentals)
    results, weights = run_grid(prices, open_prices, scores)
    write_report(results, weights, prices, scores)


if __name__ == "__main__":
    main()
