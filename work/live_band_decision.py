from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work"
sys.path.append(str(WORK))

from current_1204_order_sheet import CURRENT_1204, live_weights_from_historical  # noqa: E402
from exit_rule_comparison import add_gold_data  # noqa: E402
from medium_transform_grid import ACCOUNT_VALUE, load  # noqa: E402
from nbis_redirect_sensitivity import build_weights  # noqa: E402


DEFAULT_BAND = 0.20


def load_holdings(path: Path | None) -> pd.Series:
    if path is None:
        values = {ticker: float(row["value"]) for ticker, row in CURRENT_1204.items()}
        values["CASH"] = ACCOUNT_VALUE - sum(values.values())
        return pd.Series(values, dtype=float)
    frame = pd.read_csv(path)
    required = {"ticker", "value"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Holdings CSV missing columns: {sorted(missing)}")
    return frame.set_index("ticker")["value"].astype(float)


def latest_alt_targets() -> pd.Series:
    close, _, fundamentals = load()
    close, _ = add_gold_data(close, close)
    historical = build_weights(close, fundamentals, 0.15, 0.50, "weekly").iloc[-1]
    live = live_weights_from_historical(historical)
    return live / live.sum()


def decision(
    holdings: pd.Series,
    target_weights: pd.Series,
    band: float,
) -> tuple[float, pd.DataFrame]:
    all_tickers = sorted(set(holdings.index) | set(target_weights.index))
    current_values = holdings.reindex(all_tickers).fillna(0.0)
    total = float(current_values.sum())
    if total <= 0:
        raise ValueError("Current holdings sum to zero")
    current_weights = current_values / total
    targets = target_weights.reindex(all_tickers).fillna(0.0)
    l1 = float((current_weights - targets).abs().sum())

    rows = []
    for ticker in all_tickers:
        if ticker == "CASH" and abs(targets[ticker]) < 1e-12:
            target_value = 0.0
        else:
            target_value = total * float(targets[ticker])
        current_value = float(current_values[ticker])
        trade = target_value - current_value
        if abs(current_value) < 1 and abs(target_value) < 1 and abs(trade) < 1:
            continue
        rows.append(
            {
                "ticker": ticker,
                "current_value": current_value,
                "current_weight": float(current_weights[ticker]),
                "target_weight": float(targets[ticker]),
                "target_value": target_value,
                "trade_dollars": trade,
                "action": "BUY" if trade > 0 else "SELL" if trade < 0 else "HOLD",
            }
        )
    sheet = pd.DataFrame(rows).sort_values("trade_dollars", ascending=False)
    return l1, sheet


def main() -> None:
    parser = argparse.ArgumentParser(description="Check ALT 20% L1 band-rebalance decision.")
    parser.add_argument(
        "--holdings",
        type=Path,
        help="CSV with columns ticker,value. Defaults to 12:04 screenshot.",
    )
    parser.add_argument(
        "--band",
        type=float,
        default=DEFAULT_BAND,
        help="L1 drift trigger. Default: 0.20.",
    )
    args = parser.parse_args()

    holdings = load_holdings(args.holdings)
    target = latest_alt_targets()
    l1, sheet = decision(holdings, target, args.band)
    print(f"L1 drift: {l1:.4f}")
    print(f"Band: {args.band:.4f}")
    print(f"Decision: {'TRADE' if l1 > args.band else 'HOLD'}")
    if l1 > args.band:
        print(sheet.to_string(index=False))


if __name__ == "__main__":
    main()
