from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Holding:
    ticker: str
    shares: float = 0.0
    current_value: float | None = None
    target_weight: float | None = None
    role: str = ""


@dataclass(frozen=True)
class PortfolioConfig:
    account_name: str
    cash: float
    holdings: list[Holding]
    strategy_notes: list[str]
    watchlist: list[str]

    @property
    def tickers(self) -> list[str]:
        return [holding.ticker for holding in self.holdings]


def _as_float(raw: Any, field_name: str) -> float:
    try:
        return float(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric, got {raw!r}") from exc


def _holding_from_raw(raw: dict[str, Any]) -> Holding:
    if "ticker" not in raw:
        raise ValueError("Each holding requires a ticker")
    current_value = raw.get("current_value")
    target_weight = raw.get("target_weight")
    return Holding(
        ticker=str(raw["ticker"]).upper().strip(),
        shares=_as_float(raw.get("shares", 0.0), f"{raw['ticker']}.shares"),
        current_value=None if current_value is None else _as_float(current_value, f"{raw['ticker']}.current_value"),
        target_weight=None if target_weight is None else _as_float(target_weight, f"{raw['ticker']}.target_weight"),
        role=str(raw.get("role", "")),
    )


def load_portfolio(path: Path) -> PortfolioConfig:
    if not path.exists():
        raise FileNotFoundError(
            f"Holdings file not found: {path}. Copy config/holdings.example.json to "
            "config/holdings.local.json and fill in current shares/values."
        )

    raw = json.loads(path.read_text())
    holdings = [_holding_from_raw(item) for item in raw.get("holdings", [])]
    if not holdings:
        raise ValueError(f"{path} must contain at least one holding")

    target_total = sum(holding.target_weight or 0.0 for holding in holdings)
    if target_total > 1.001:
        raise ValueError(f"Target weights sum above 100%: {target_total:.4f}")

    return PortfolioConfig(
        account_name=str(raw.get("account_name", "taxable")),
        cash=_as_float(raw.get("cash", 0.0), "cash"),
        holdings=holdings,
        strategy_notes=[str(item) for item in raw.get("strategy_notes", [])],
        watchlist=[str(item).upper() for item in raw.get("watchlist", [])],
    )
