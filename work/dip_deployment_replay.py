from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yfinance as yf


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
START = "2016-01-01"
END = "2026-07-02"
DEPLOY_CASH = 60_000.0
TRANCHE_SIZE = 20_000.0
TRANCHE_SPACING_DAYS = 5
HORIZON_DAYS = 252

BASE_VALUES = {
    "QQQ": 68_893.20,
    "MU": 62_221.36,
    "NBIS_PROXY": 46_168.91,
    "DRAM_PROXY": 20_424.36,
    "NVDA": 19_759.61,
}


@dataclass(frozen=True)
class Episode:
    name: str
    start: str
    end: str


EPISODES = [
    Episode("2018_top", "2018-08-01", "2019-03-31"),
    Episode("2020_covid_v", "2020-02-01", "2020-05-31"),
    Episode("2022_top", "2021-11-01", "2022-06-30"),
    Episode("2025_ignition", "2025-01-01", "2025-12-31"),
]


def download_prices() -> pd.DataFrame:
    data = yf.download(["QQQ", "MU", "NVDA", "STX"], start=START, end=END, auto_adjust=True, progress=False)
    close = data["Close"].dropna(how="all")
    returns = close.pct_change().fillna(0.0)
    close["NBIS_PROXY"] = (1.0 + (returns["NVDA"] * 1.5).clip(lower=-0.85)).cumprod()
    close["DRAM_PROXY"] = (1.0 + returns["MU"] * 0.75 + returns["STX"] * 0.25).cumprod()
    return close[["QQQ", "MU", "NVDA", "NBIS_PROXY", "DRAM_PROXY"]].dropna()


def first_mu_drop(prices: pd.DataFrame, episode: Episode) -> pd.Timestamp | None:
    returns = prices["MU"].pct_change()
    window = returns.loc[episode.start : episode.end]
    hits = window[window <= -0.08]
    if hits.empty:
        return None
    return pd.Timestamp(hits.index[0])


def basket_value(prices: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> float:
    total = 0.0
    for ticker, value in BASE_VALUES.items():
        total += value * float(prices.loc[end, ticker] / prices.loc[start, ticker])
    return total


def staged_mu_value(prices: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> float:
    value = 0.0
    start_index = prices.index.get_loc(start)
    if not isinstance(start_index, int):
        start_index = int(start_index.start)
    for offset in [0, TRANCHE_SPACING_DAYS, TRANCHE_SPACING_DAYS * 2]:
        buy_index = min(start_index + offset, len(prices) - 1)
        buy_date = prices.index[buy_index]
        value += TRANCHE_SIZE * float(prices.loc[end, "MU"] / prices.loc[buy_date, "MU"])
    return value


def replay_episode(prices: pd.DataFrame, episode: Episode) -> dict[str, object]:
    trigger = first_mu_drop(prices, episode)
    if trigger is None:
        return {"episode": episode.name, "trigger": None}
    start_index = prices.index.get_loc(trigger)
    if not isinstance(start_index, int):
        start_index = int(start_index.start)
    end_index = min(start_index + HORIZON_DAYS, len(prices) - 1)
    end = pd.Timestamp(prices.index[end_index])
    hold_cash = basket_value(prices, trigger, end) + DEPLOY_CASH
    all_in = basket_value(prices, trigger, end) + DEPLOY_CASH * float(prices.loc[end, "MU"] / prices.loc[trigger, "MU"])
    staged = basket_value(prices, trigger, end) + staged_mu_value(prices, trigger, end)
    return {
        "episode": episode.name,
        "trigger": trigger.date().isoformat(),
        "horizon_end": end.date().isoformat(),
        "all_in_vs_cash": all_in - hold_cash,
        "staged_vs_cash": staged - hold_cash,
        "staged_minus_all_in": staged - all_in,
    }


def main() -> None:
    OUT.mkdir(exist_ok=True)
    prices = download_prices()
    rows = [replay_episode(prices, episode) for episode in EPISODES]
    frame = pd.DataFrame(rows)
    frame.to_csv(OUT / "dip_deployment_replay.csv", index=False)
    print(frame.to_string(index=False))


if __name__ == "__main__":
    main()
