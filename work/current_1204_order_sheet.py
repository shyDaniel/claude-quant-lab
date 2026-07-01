from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work"
OUT = ROOT / "outputs"
sys.path.append(str(WORK))

from exit_rule_comparison import add_gold_data, current_final_weights, replace_defensive_asset  # noqa: E402
from medium_transform_grid import ACCOUNT_VALUE, load  # noqa: E402


CURRENT_1204 = {
    "QQQ": {"shares": 95.00, "value": 68_893.20},
    "NBIS": {"shares": 199.00, "value": 46_168.91},
    "MU": {"shares": 27.00, "value": 27_999.61},
    "DRAM": {"shares": 308.01, "value": 20_424.36},
    "NVDA": {"shares": 100.01, "value": 19_759.61},
    "SMCI": {"shares": 300.00, "value": 8_355.00},
}


def live_weights_from_historical(final_weights: pd.Series) -> pd.Series:
    live = final_weights.copy()
    if "DRAM" not in live.index:
        live.loc["DRAM"] = 0.0
    live.loc["DRAM"] += float(live.get("SNDK", 0.0))
    for ticker in ["SNDK", "STX", "BIL"]:
        if ticker in live.index:
            live.loc[ticker] = 0.0
    return live[live > 0].sort_values(ascending=False)


def build_order_sheet() -> pd.DataFrame:
    close, open_, fundamentals = load()
    close, open_ = add_gold_data(close, open_)
    target_weights = live_weights_from_historical(
        replace_defensive_asset(current_final_weights(close, fundamentals), "GLD").iloc[-1]
    )

    price_row = close.loc[close.index.max()]
    rows: list[dict[str, float | str]] = []
    for ticker, target_weight in target_weights.items():
        current = CURRENT_1204.get(ticker, {"shares": 0.0, "value": 0.0})
        current_shares = float(current["shares"])
        current_value = float(current["value"])
        if current_shares > 0:
            price = current_value / current_shares
        else:
            price = float(price_row[ticker])
        target_value = ACCOUNT_VALUE * float(target_weight)
        trade_dollars = target_value - current_value
        rows.append(
            {
                "ticker": ticker,
                "current_shares": current_shares,
                "current_value": current_value,
                "target_value": target_value,
                "trade_dollars": trade_dollars,
                "approx_price_used": price,
                "approx_shares_to_trade": trade_dollars / price,
                "target_weight": float(target_weight),
                "action": "BUY" if trade_dollars > 0 else "SELL",
            }
        )

    return pd.DataFrame(rows).sort_values("trade_dollars", ascending=False)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    sheet = build_order_sheet()
    sheet.to_csv(OUT / "current_1204_exact_order_sheet_GLD_defensive.csv", index=False)
    print(sheet.to_string(index=False))


if __name__ == "__main__":
    main()
