from __future__ import annotations

from pathlib import Path

import pandas as pd
import yfinance as yf


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
START = "2004-01-01"
END = "2026-07-02"
TICKERS = ["MU", "NBIS"]


def download_close(ticker: str) -> pd.Series:
    data = yf.download(ticker, start=START, end=END, auto_adjust=True, progress=False)
    if data.empty:
        raise ValueError(f"No price data returned for {ticker}")
    close = data["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    return close.dropna().rename(ticker)


def forward_return(close: pd.Series, event_date: pd.Timestamp, days: int) -> float | None:
    index = close.index.get_loc(event_date)
    if not isinstance(index, int):
        index = int(index.start)
    end_index = index + days
    if end_index >= len(close):
        return None
    return float(close.iloc[end_index] / close.iloc[index] - 1.0)


def build_events(close: pd.Series, threshold: float) -> pd.DataFrame:
    returns = close.pct_change()
    ma_200 = close.rolling(200).mean()
    rows: list[dict[str, object]] = []
    for date, daily_return in returns[returns <= threshold].items():
        rows.append(
            {
                "date": date.date().isoformat(),
                "ticker": close.name,
                "daily_return": float(daily_return),
                "above_200dma": bool(close.loc[date] > ma_200.loc[date]),
                "fwd_21d": forward_return(close, date, 21),
                "fwd_63d": forward_return(close, date, 63),
                "fwd_126d": forward_return(close, date, 126),
                "fwd_252d": forward_return(close, date, 252),
            }
        )
    return pd.DataFrame(rows)


def summarize(events: pd.DataFrame, close: pd.Series) -> pd.DataFrame:
    baseline = pd.DataFrame(
        {
            "bucket": ["baseline_all_dates"],
            "events": [len(close)],
            "median_6m": [_median_forward(close, 126)],
            "median_12m": [_median_forward(close, 252)],
        }
    )
    grouped = []
    for bucket, frame in {
        "all_drop_events": events,
        "above_200dma": events[events["above_200dma"]],
        "below_200dma": events[~events["above_200dma"]],
    }.items():
        grouped.append(
            {
                "bucket": bucket,
                "events": len(frame),
                "median_6m": frame["fwd_126d"].median(),
                "median_12m": frame["fwd_252d"].median(),
            }
        )
    return pd.concat([baseline, pd.DataFrame(grouped)], ignore_index=True)


def _median_forward(close: pd.Series, days: int) -> float:
    values = close.shift(-days) / close - 1.0
    return float(values.dropna().median())


def main() -> None:
    OUT.mkdir(exist_ok=True)
    all_events: list[pd.DataFrame] = []
    summaries: list[pd.DataFrame] = []
    for ticker in TICKERS:
        close = download_close(ticker)
        events = build_events(close, -0.08 if ticker == "MU" else -0.10)
        all_events.append(events)
        summary = summarize(events, close)
        summary.insert(0, "ticker", ticker)
        summaries.append(summary)

    events_frame = pd.concat(all_events, ignore_index=True)
    summary_frame = pd.concat(summaries, ignore_index=True)
    events_frame.to_csv(OUT / "mu_nbis_drop_events.csv", index=False)
    summary_frame.to_csv(OUT / "mu_nbis_drop_event_summary.csv", index=False)
    print(summary_frame.to_string(index=False))


if __name__ == "__main__":
    main()
