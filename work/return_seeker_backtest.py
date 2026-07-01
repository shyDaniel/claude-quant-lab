from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
CACHE = ROOT / "work" / "cache"
TRADING_DAYS = 252
START_CAPITAL = 278_726.16
BUYING_POWER = 102_555.39

SCREENSHOT_HOLDINGS = {
    "QQQ": (100.00, 728.39),
    "NBIS": (120.00, 234.92),
    "MU": (25.00, 1063.06),
    "DRAM": (300.01, 67.02),
    "NVDA": (100.01, 199.53),
    "SMCI": (300.00, 28.16),
}

AI_UNIVERSE = [
    "NVDA",
    "AMD",
    "AVGO",
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

BACKTEST_TICKERS = sorted(set(["QQQ", "BIL", "DRAM"] + AI_UNIVERSE))


@dataclass(frozen=True)
class BacktestResult:
    strategy: str
    window: str
    start: str
    end: str
    cagr: float
    sharpe: float
    max_drawdown: float
    worst_12m: float
    volatility: float
    turnover: float
    end_value: float


def download_prices() -> pd.DataFrame:
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / "return_seeker_prices.csv"
    raw = yf.download(
        BACKTEST_TICKERS,
        start="2014-01-01",
        auto_adjust=True,
        progress=False,
        threads=False,
    )
    close = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw
    close = close.dropna(how="all").sort_index()
    close.index.name = "Date"
    close.to_csv(path)
    return close


def month_end_mask(index: pd.DatetimeIndex) -> pd.Series:
    return index.to_series().groupby(index.to_period("M")).transform("max") == index


def current_values() -> pd.DataFrame:
    rows = []
    for ticker, (shares, price) in SCREENSHOT_HOLDINGS.items():
        value = shares * price
        rows.append(
            {
                "ticker": ticker,
                "shares": shares,
                "screenshot_price": price,
                "value": value,
                "weight": value / START_CAPITAL,
            }
        )
    rows.append(
        {
            "ticker": "CASH",
            "shares": np.nan,
            "screenshot_price": np.nan,
            "value": BUYING_POWER,
            "weight": BUYING_POWER / START_CAPITAL,
        }
    )
    return pd.DataFrame(rows)


def simulate(weights: pd.DataFrame, prices: pd.DataFrame, cost_bps: float = 5.0) -> tuple[pd.Series, float]:
    sub = prices.reindex(columns=weights.columns)
    returns = sub.pct_change().fillna(0.0)
    aligned = weights.reindex(sub.index).fillna(0.0)
    gross = (aligned.shift(1).fillna(0.0) * returns).sum(axis=1)
    turnover = aligned.diff().abs().sum(axis=1).fillna(0.0)
    net = gross - turnover * cost_bps / 10_000.0
    ann_turnover = turnover.sum() / max(len(sub) / TRADING_DAYS, 1.0)
    return net, ann_turnover


def static_mix(prices: pd.DataFrame, allocations: dict[str, float]) -> tuple[pd.Series, float]:
    weights = pd.DataFrame(index=prices.index, columns=allocations.keys(), dtype=float)
    for ticker, weight in allocations.items():
        weights[ticker] = weight
    weights = weights.fillna(0.0)
    return simulate(weights, prices[list(allocations.keys())], cost_bps=2.0)


def ai_trend_weights(prices: pd.DataFrame, ai_weight: float, qqq_weight: float, cash_weight: float) -> pd.DataFrame:
    ai_names = [name for name in AI_UNIVERSE if name in prices.columns]
    px = prices[ai_names]
    above = px > px.rolling(100).mean()
    valid = px.rolling(100).count().ge(100)
    basket_nav = (1.0 + px.pct_change().mean(axis=1).fillna(0.0)).cumprod()
    basket_gate = basket_nav > basket_nav.rolling(100).mean()
    on = above & valid
    on = on.mul(basket_gate, axis=0)
    counts = on.sum(axis=1).replace(0, np.nan)
    ai_weights = on.div(counts, axis=0).fillna(0.0) * ai_weight
    weights = ai_weights.copy()
    weights["QQQ"] = qqq_weight
    weights["BIL"] = cash_weight + (ai_weight - ai_weights.sum(axis=1))
    return weights


def metrics(name: str, window: str, returns: pd.Series, turnover: float) -> BacktestResult:
    d = returns.dropna()
    equity = (1.0 + d).cumprod()
    years = len(d) / TRADING_DAYS
    return BacktestResult(
        strategy=name,
        window=window,
        start=str(d.index[0].date()),
        end=str(d.index[-1].date()),
        cagr=equity.iloc[-1] ** (1.0 / years) - 1.0,
        sharpe=d.mean() / d.std() * np.sqrt(TRADING_DAYS) if d.std() > 0 else np.nan,
        max_drawdown=(equity / equity.cummax() - 1.0).min(),
        worst_12m=equity.pct_change(TRADING_DAYS).min(),
        volatility=d.std() * np.sqrt(TRADING_DAYS),
        turnover=turnover,
        end_value=START_CAPITAL * equity.iloc[-1],
    )


def build_strategies(prices: pd.DataFrame) -> dict[str, tuple[pd.Series, float]]:
    current = current_values()
    invested = current[current["ticker"] != "CASH"].set_index("ticker")["weight"].to_dict()
    current_returns, current_turn = static_mix(prices, invested)
    all_in_current = {ticker: weight / (1.0 - BUYING_POWER / START_CAPITAL) for ticker, weight in invested.items()}
    all_in_returns, all_in_turn = static_mix(prices, all_in_current)
    qqq_returns, qqq_turn = static_mix(prices, {"QQQ": 1.0})
    out = {
        "Current holdings, cash ignored": (current_returns, current_turn),
        "Current names, deploy all cash pro-rata": (all_in_returns, all_in_turn),
        "QQQ buy-hold": (qqq_returns, qqq_turn),
    }
    for ai_weight, qqq_weight, cash_weight in [
        (0.50, 0.45, 0.05),
        (0.60, 0.35, 0.05),
        (0.70, 0.25, 0.05),
        (0.75, 0.20, 0.05),
    ]:
        weights = ai_trend_weights(prices, ai_weight, qqq_weight, cash_weight)
        returns, turn = simulate(weights, prices[weights.columns], cost_bps=10.0)
        name = f"{int(ai_weight*100)}% AI trend / {int(qqq_weight*100)}% QQQ / {int(cash_weight*100)}% cash"
        out[name] = (returns, turn)
    return out


def signal_table(prices: pd.DataFrame) -> pd.DataFrame:
    rows = []
    last = prices.index.max()
    for ticker in ["QQQ"] + AI_UNIVERSE + ["DRAM"]:
        if ticker not in prices.columns:
            continue
        series = prices[ticker].dropna()
        if len(series) < 130:
            continue
        price = series.iloc[-1]
        ma100 = series.rolling(100).mean().iloc[-1]
        mom_6m = price / series.shift(126).iloc[-1] - 1.0
        ret_20d = price / series.shift(20).iloc[-1] - 1.0
        rows.append(
            {
                "ticker": ticker,
                "price": price,
                "above_100d": bool(price > ma100),
                "dist_100d": price / ma100 - 1.0,
                "mom_6m": mom_6m,
                "ret_20d": ret_20d,
            }
        )
    return pd.DataFrame(rows).sort_values("mom_6m", ascending=False)


def target_trade_table(signal: pd.DataFrame) -> pd.DataFrame:
    total = START_CAPITAL
    current = current_values().set_index("ticker")
    qqq_current = current.loc["QQQ", "value"]
    cash_target = 0.05 * total
    qqq_target = qqq_current
    ai_budget = total - cash_target - qqq_target
    buys = signal[(signal["ticker"].isin(AI_UNIVERSE)) & (signal["above_100d"])].copy()
    avoid_extra = {"NBIS", "SMCI"}
    buys = buys[~buys["ticker"].isin(avoid_extra)]
    buys = buys.head(9)
    per_name_target = ai_budget / max(len(buys), 1)
    rows = []
    for _, row in buys.iterrows():
        ticker = row["ticker"]
        held = current.loc[ticker, "value"] if ticker in current.index else 0.0
        buy = max(per_name_target - held, 0.0)
        rows.append(
            {
                "ticker": ticker,
                "current_value": held,
                "target_value": per_name_target,
                "suggested_buy_dollars": buy,
                "signal": "above 100d, high 6m momentum",
            }
        )
    trades = pd.DataFrame(rows)
    scale = min((BUYING_POWER - cash_target) / trades["suggested_buy_dollars"].sum(), 1.0)
    trades["suggested_buy_dollars"] = trades["suggested_buy_dollars"] * max(scale, 0.0)
    return trades.sort_values("suggested_buy_dollars", ascending=False)


def write_outputs(results: list[BacktestResult], signal: pd.DataFrame, trades: pd.DataFrame) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    result_df = pd.DataFrame([row.__dict__ for row in results])
    result_df.to_csv(OUT / "return_seeker_metrics.csv", index=False)
    display = result_df.copy()
    for col in ["cagr", "max_drawdown", "worst_12m", "volatility"]:
        display[col] = display[col].map(lambda x: f"{x*100:.1f}%")
    display["sharpe"] = display["sharpe"].map(lambda x: f"{x:.2f}")
    display["turnover"] = display["turnover"].map(lambda x: f"{x:.1f}x")
    display["end_value"] = display["end_value"].map(lambda x: f"${x:,.0f}")
    display.to_markdown(OUT / "return_seeker_metrics.md", index=False)
    signal.to_csv(OUT / "return_seeker_signals.csv", index=False)
    trades.to_csv(OUT / "return_seeker_trade_plan.csv", index=False)
    current = current_values()
    current.to_csv(OUT / "current_portfolio_from_screenshot.csv", index=False)

    top_5y = result_df[result_df["window"] == "5y"].sort_values("sharpe", ascending=False).head(5)
    top_10y = result_df[result_df["window"] == "10y"].sort_values("sharpe", ascending=False).head(5)
    report = [
        "# Return-Seeking AI Portfolio Update",
        "",
        "## Current Portfolio From Screenshots",
        current.to_markdown(index=False, floatfmt=".2f"),
        "",
        "## Backtest Takeaway",
        "For a 26-year-old return seeker, the cash drag is the clearest issue. The AI-heavy trend",
        "variants beat QQQ historically, but they remain survivorship-biased because they use today's",
        "known AI winners. The most practical aggressive update is to keep existing QQQ and deploy",
        "most cash into a diversified AI sleeve, rather than adding more QQQ today.",
        "",
        "## Top 5-Year Rows",
        top_5y.to_markdown(index=False),
        "",
        "## Top 10-Year Rows",
        top_10y.to_markdown(index=False),
        "",
        "## Current Signals",
        signal.to_markdown(index=False, floatfmt=".2f"),
        "",
        "## Rule-Based Buy Plan",
        "Target: keep current 100 QQQ shares, keep about 5% cash, deploy the rest into AI names",
        "that are above their 100-day moving average. Do not add more NBIS or SMCI in this pass;",
        "they are already concentrated/speculative in the current account.",
        "",
        trades.to_markdown(index=False, floatfmt=".2f"),
        "",
        "## Guardrails",
        "- This is not personalized fiduciary advice or an order ticket.",
        "- Do not market-order thin or volatile names all at once; use limit orders or staged buys.",
        "- If the AI sleeve drops below its 100-day/basket trend rule, the model says cut risk.",
        "- A 70% AI allocation can lose 35-50% of the account in a true theme crash.",
    ]
    (OUT / "RETURN_SEEKER_PLAN.md").write_text("\n".join(report) + "\n")


def main() -> None:
    prices = download_prices()
    strategies = build_strategies(prices)
    windows = {"5y": "2021-07-01", "10y": "2016-07-01", "full": "2014-01-01"}
    rows = []
    for window, start in windows.items():
        for name, (returns, turnover) in strategies.items():
            rows.append(metrics(name, window, returns.loc[start:], turnover))
    signal = signal_table(prices)
    trades = target_trade_table(signal)
    write_outputs(rows, signal, trades)


if __name__ == "__main__":
    main()
