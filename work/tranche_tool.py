from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGETS_PATH = ROOT / "config" / "v3_targets.json"

REFERENCE_VALUES = {
    "QQQ": 68_893.20,
    "MU": 62_221.36,
    "NBIS": 46_168.91,
    "DRAM": 20_424.36,
    "NVDA": 19_759.61,
    "GEV": 0.0,
    "VRT": 0.0,
    "GLD": 0.0,
    "CASH": 59_754.09,
}


@dataclass(frozen=True)
class Target:
    ticker: str
    weight: float
    buy_allowed: bool
    role: str


def load_targets(path: Path) -> dict[str, Target]:
    raw = json.loads(path.read_text())
    targets: dict[str, Target] = {}
    for item in raw["targets"]:
        target = Target(
            ticker=str(item["ticker"]).upper(),
            weight=float(item["target_weight"]),
            buy_allowed=bool(item.get("buy_allowed", True)),
            role=str(item.get("role", "")),
        )
        targets[target.ticker] = target
    total = sum(target.weight for target in targets.values())
    if abs(total - 1.0) > 0.002:
        raise ValueError(f"Target weights should sum to 100%, got {total:.4f}")
    return targets


def load_values(path: Path | None) -> pd.Series:
    if path is None:
        return pd.Series(REFERENCE_VALUES, dtype=float)
    if path.suffix.lower() == ".json":
        return _load_json_values(path)
    frame = pd.read_csv(path)
    required = {"ticker", "value"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"{path} missing columns: {sorted(missing)}")
    return frame.set_index("ticker")["value"].astype(float).rename(index=str.upper)


def _load_json_values(path: Path) -> pd.Series:
    raw = json.loads(path.read_text())
    values: dict[str, float] = {"CASH": float(raw.get("cash", 0.0))}
    for holding in raw.get("holdings", []):
        ticker = str(holding["ticker"]).upper()
        if "current_value" in holding:
            values[ticker] = float(holding["current_value"])
        else:
            values[ticker] = 0.0
    return pd.Series(values, dtype=float)


def build_tranche(
    values: pd.Series,
    targets: dict[str, Target],
    cash_to_deploy: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    tickers = sorted(set(values.index) | set(targets))
    current = values.reindex(tickers).fillna(0.0)
    account_value = float(current.sum())
    deploy = min(cash_to_deploy, float(current.get("CASH", cash_to_deploy)), account_value)
    if deploy <= 0:
        raise ValueError("No positive cash is available to deploy")

    rows: list[dict[str, Any]] = []
    for ticker in tickers:
        if ticker == "CASH":
            continue
        target = targets.get(ticker, Target(ticker, 0.0, False, "not in target"))
        target_value = account_value * target.weight
        current_value = float(current.get(ticker, 0.0))
        underweight = target_value - current_value
        rows.append(
            {
                "ticker": ticker,
                "current_value": current_value,
                "current_weight": current_value / account_value,
                "target_weight": target.weight,
                "target_value": target_value,
                "underweight_dollars": underweight,
                "buy_allowed": target.buy_allowed,
                "role": target.role,
            }
        )
    ranking = pd.DataFrame(rows).sort_values("underweight_dollars", ascending=False)

    eligible = ranking[(ranking["buy_allowed"]) & (ranking["underweight_dollars"] > 0)].copy()
    total_need = float(eligible["underweight_dollars"].sum())
    if total_need <= 0:
        return ranking, pd.DataFrame(columns=["ticker", "buy_dollars", "reason"])

    eligible["buy_dollars"] = eligible["underweight_dollars"] / total_need * deploy
    eligible["buy_dollars"] = eligible["buy_dollars"].clip(upper=eligible["underweight_dollars"])
    eligible["reason"] = "most-underweight allowed target"
    order = eligible[["ticker", "buy_dollars", "underweight_dollars", "target_weight", "reason"]]
    return ranking, order.sort_values("buy_dollars", ascending=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the next v3 underweight-seeking tranche.")
    parser.add_argument("--targets", type=Path, default=DEFAULT_TARGETS_PATH)
    parser.add_argument("--holdings", type=Path, help="CSV ticker,value or holdings JSON. Defaults to handoff snapshot.")
    parser.add_argument("--cash-to-deploy", type=float, default=20_000.0)
    args = parser.parse_args()

    targets = load_targets(args.targets)
    values = load_values(args.holdings)
    ranking, order = build_tranche(values, targets, args.cash_to_deploy)

    print("Most-underweight ranking:")
    print(
        ranking[
            ["ticker", "current_weight", "target_weight", "underweight_dollars", "buy_allowed"]
        ].to_string(index=False, formatters={
            "current_weight": "{:.2%}".format,
            "target_weight": "{:.2%}".format,
            "underweight_dollars": "${:,.2f}".format,
        })
    )
    print("\nNext tranche order sheet:")
    if order.empty:
        print("HOLD: no allowed underweights.")
    else:
        print(
            order.to_string(index=False, formatters={
                "buy_dollars": "${:,.2f}".format,
                "underweight_dollars": "${:,.2f}".format,
                "target_weight": "{:.2%}".format,
            })
        )


if __name__ == "__main__":
    main()
