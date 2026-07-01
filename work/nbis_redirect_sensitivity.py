from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work"
OUT = ROOT / "outputs"
sys.path.append(str(WORK))

from current_1204_order_sheet import CURRENT_1204, live_weights_from_historical  # noqa: E402
from exit_rule_comparison import add_gold_data, calc_metrics, replace_defensive_asset  # noqa: E402
from medium_transform_grid import ACCOUNT_VALUE, START, load, sim, weights  # noqa: E402
from nbis_storage_tilt_grid import BASE_ARGS, active_masks, overlay_weights  # noqa: E402
from smci_keep_backtest import SMCI_CURRENT_WEIGHT, apply_smci_floor  # noqa: E402


VARIANTS = [
    {
        "name": "selected_weekly_floor25_redirect100",
        "nbis_floor": 0.25,
        "storage_redirect": 1.00,
        "cadence": "weekly",
    },
    {
        "name": "alt_weekly_floor15_redirect50",
        "nbis_floor": 0.15,
        "storage_redirect": 0.50,
        "cadence": "weekly",
    },
    {
        "name": "alt_monthly_floor15_redirect50",
        "nbis_floor": 0.15,
        "storage_redirect": 0.50,
        "cadence": "monthly",
    },
]


def build_weights(
    close: pd.DataFrame,
    fundamentals: pd.DataFrame,
    nbis_floor: float,
    storage_redirect: float,
    cadence: str,
) -> pd.DataFrame:
    args = {**BASE_ARGS, "cadence": cadence}
    base = weights(close, fundamentals, **args)
    trend_active, tradable = active_masks(close)
    with_nbis = overlay_weights(
        base,
        trend_active,
        tradable,
        nbis_floor,
        0.30,
        storage_redirect,
        "tradable",
    )
    with_smci = apply_smci_floor(
        with_nbis,
        trend_active,
        tradable,
        SMCI_CURRENT_WEIGHT,
        "tradable",
    )
    return replace_defensive_asset(with_smci, "GLD")


def order_sheet(strategy: str, latest_weights: pd.Series, close: pd.DataFrame) -> pd.DataFrame:
    live = live_weights_from_historical(latest_weights)
    price_row = close.loc[close.index.max()]
    rows: list[dict[str, float | str]] = []
    for ticker, target_weight in live.items():
        current = CURRENT_1204.get(ticker, {"shares": 0.0, "value": 0.0})
        current_shares = float(current["shares"])
        current_value = float(current["value"])
        price = current_value / current_shares if current_shares > 0 else float(price_row[ticker])
        target_value = ACCOUNT_VALUE * float(target_weight)
        trade_dollars = target_value - current_value
        rows.append(
            {
                "strategy": strategy,
                "ticker": ticker,
                "target_weight": float(target_weight),
                "current_value": current_value,
                "target_value": target_value,
                "trade_dollars": trade_dollars,
                "approx_price_used": price,
                "approx_shares_to_trade": trade_dollars / price,
                "action": "BUY" if trade_dollars > 0 else "SELL",
            }
        )
    return pd.DataFrame(rows).sort_values("target_value", ascending=False)


def main() -> None:
    close, open_, fundamentals = load()
    close, open_ = add_gold_data(close, open_)
    rows = []
    sheets = []
    curves: dict[str, pd.Series] = {}

    for variant in VARIANTS:
        w = build_weights(
            close,
            fundamentals,
            float(variant["nbis_floor"]),
            float(variant["storage_redirect"]),
            str(variant["cadence"]),
        )
        daily, turn = sim(close, open_, w, "close")
        latest = w.iloc[-1]
        rows.append(
            {
                **variant,
                **calc_metrics(daily, turn, START),
                "current_nbis_weight": float(latest["NBIS"]),
                "current_storage_weight": float(latest[["MU", "SNDK", "STX"]].sum()),
                "current_gld_weight": float(latest["GLD"]),
                "current_smci_weight": float(latest["SMCI"]),
            }
        )
        sheets.append(order_sheet(str(variant["name"]), latest, close))
        curves[str(variant["name"])] = (1 + daily.loc[START:]).cumprod()

    results = pd.DataFrame(rows)
    orders = pd.concat(sheets, ignore_index=True)
    OUT.mkdir(exist_ok=True)
    results.to_csv(OUT / "nbis_redirect_sensitivity_results.csv", index=False)
    orders.to_csv(OUT / "nbis_redirect_sensitivity_order_sheets.csv", index=False)
    orders[orders["strategy"] == "alt_weekly_floor15_redirect50"].to_csv(
        OUT / "alternative_nbis_redirect_order_sheet.csv",
        index=False,
    )

    selected = results.loc[results["name"] == "selected_weekly_floor25_redirect100"].iloc[0]
    alt = results.loc[results["name"] == "alt_weekly_floor15_redirect50"].iloc[0]
    monthly = results.loc[results["name"] == "alt_monthly_floor15_redirect50"].iloc[0]
    alt_orders = orders.loc[orders["strategy"] == "alt_weekly_floor15_redirect50"]

    lines = [
        "# NBIS Redirect Sensitivity",
        "",
        "Date: 2026-07-01",
        "",
        "## Why This Exists",
        "",
        "Claude's audit correctly flagged that today's 26.45% NBIS weight is not mainly the explicit 25% floor. The base model's memory/storage exposure exceeds the 30% storage cap, and the selected `storage_excess_to_nbis=1.00` parameter redirects that excess into NBIS.",
        "",
        "This file tests a less extreme variant: NBIS floor 15% and storage redirect 50%, while keeping QQQ, GLD, SMCI, DRAM substitution, storage cap, scoring, and trend rules otherwise unchanged.",
        "",
        "## Results",
        "",
        "| Strategy | CAGR | Sharpe | MaxDD | Worst 12m | Turnover | NBIS | Storage | GLD |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, row in results.iterrows():
        lines.append(
            f"| {row['name']} | {row['cagr'] * 100:.2f}% | {row['sharpe']:.2f} | "
            f"{row['max_drawdown'] * 100:.2f}% | {row['worst_12m'] * 100:.2f}% | "
            f"{row['turnover']:.2f}x | {row['current_nbis_weight'] * 100:.2f}% | "
            f"{row['current_storage_weight'] * 100:.2f}% | {row['current_gld_weight'] * 100:.2f}% |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"- Selected weekly model: CAGR {selected.cagr * 100:.2f}%, NBIS {selected.current_nbis_weight * 100:.2f}%, turnover {selected.turnover:.2f}x.",
            f"- Lower-redirect weekly model: CAGR {alt.cagr * 100:.2f}%, NBIS {alt.current_nbis_weight * 100:.2f}%, turnover {alt.turnover:.2f}x.",
            f"- Lower-redirect monthly model: CAGR {monthly.cagr * 100:.2f}%, NBIS {monthly.current_nbis_weight * 100:.2f}%, turnover {monthly.turnover:.2f}x.",
            "",
            "The lower-redirect variant gives up some backtested CAGR but reduces single-name NBIS concentration. That trade is small relative to the known survivorship, lookahead, tax, and short-history uncertainties.",
            "",
            "## Alternative Weekly Target Weights",
            "",
            alt_orders[["ticker", "target_weight", "target_value", "trade_dollars", "approx_shares_to_trade", "action"]].to_markdown(index=False, floatfmt=".4f"),
            "",
            "## Files",
            "",
            "- `outputs/nbis_redirect_sensitivity_results.csv`",
            "- `outputs/nbis_redirect_sensitivity_order_sheets.csv`",
            "- `outputs/alternative_nbis_redirect_order_sheet.csv`",
        ]
    )
    (OUT / "NBIS_REDIRECT_SENSITIVITY.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
