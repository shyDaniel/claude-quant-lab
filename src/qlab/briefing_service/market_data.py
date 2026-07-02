from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import pandas as pd
import yfinance as yf

from qlab.briefing_service.holdings import PortfolioConfig


INDEX_TICKERS = ["QQQ", "SPY", "IWM", "GLD", "TLT", "^VIX"]


@dataclass(frozen=True)
class QuoteStats:
    ticker: str
    price: float | None
    one_day: float | None
    five_day: float | None
    twenty_day: float | None
    vs_100dma: float | None
    vs_200dma: float | None


def _pct_change(series: pd.Series, periods: int) -> float | None:
    clean = series.dropna()
    if len(clean) <= periods:
        return None
    return float(clean.iloc[-1] / clean.iloc[-1 - periods] - 1.0)


def _moving_average_gap(series: pd.Series, window: int) -> float | None:
    clean = series.dropna()
    if len(clean) < window:
        return None
    average = float(clean.rolling(window).mean().iloc[-1])
    if average <= 0:
        return None
    return float(clean.iloc[-1] / average - 1.0)


def _stats_for(ticker: str, close: pd.DataFrame) -> QuoteStats:
    if ticker not in close.columns:
        return QuoteStats(ticker, None, None, None, None, None, None)
    series = close[ticker].dropna()
    if series.empty:
        return QuoteStats(ticker, None, None, None, None, None, None)
    return QuoteStats(
        ticker=ticker,
        price=float(series.iloc[-1]),
        one_day=_pct_change(series, 1),
        five_day=_pct_change(series, 5),
        twenty_day=_pct_change(series, 20),
        vs_100dma=_moving_average_gap(series, 100),
        vs_200dma=_moving_average_gap(series, 200),
    )


def _download_close(tickers: list[str]) -> pd.DataFrame:
    data = yf.download(
        sorted(set(tickers)),
        period="1y",
        auto_adjust=True,
        progress=False,
        threads=True,
    )
    if data.empty:
        return pd.DataFrame()
    if isinstance(data.columns, pd.MultiIndex):
        return data["Close"].copy()
    return data[["Close"]].rename(columns={"Close": tickers[0]})


def build_market_context(portfolio: PortfolioConfig) -> dict[str, Any]:
    tickers = portfolio.tickers + portfolio.watchlist + INDEX_TICKERS
    close = _download_close(tickers)
    stats = {ticker: _stats_for(ticker, close) for ticker in sorted(set(tickers))}

    holding_rows: list[dict[str, Any]] = []
    account_value = float(portfolio.cash)
    for holding in portfolio.holdings:
        stat = stats.get(holding.ticker)
        market_value = holding.current_value
        if market_value is None and stat and stat.price is not None:
            market_value = holding.shares * stat.price
        market_value = 0.0 if market_value is None else float(market_value)
        account_value += market_value
        holding_rows.append(
            {
                "ticker": holding.ticker,
                "shares": holding.shares,
                "market_value": market_value,
                "target_weight": holding.target_weight,
                "role": holding.role,
                "price": None if stat is None else stat.price,
                "one_day": None if stat is None else stat.one_day,
                "five_day": None if stat is None else stat.five_day,
                "twenty_day": None if stat is None else stat.twenty_day,
                "vs_100dma": None if stat is None else stat.vs_100dma,
                "vs_200dma": None if stat is None else stat.vs_200dma,
            }
        )

    for row in holding_rows:
        row["current_weight"] = row["market_value"] / account_value if account_value > 0 else None
        target = row["target_weight"]
        row["weight_gap"] = None if target is None or row["current_weight"] is None else target - row["current_weight"]

    return {
        "as_of_utc": datetime.now(UTC).isoformat(),
        "account_name": portfolio.account_name,
        "cash": portfolio.cash,
        "account_value": account_value,
        "holdings": holding_rows,
        "indices": {
            ticker: stats[ticker].__dict__
            for ticker in INDEX_TICKERS
            if ticker in stats
        },
        "watchlist": {
            ticker: stats[ticker].__dict__
            for ticker in portfolio.watchlist
            if ticker in stats
        },
        "strategy_notes": portfolio.strategy_notes,
    }
