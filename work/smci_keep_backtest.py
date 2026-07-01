from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work"
OUT = ROOT / "outputs"
sys.path.append(str(WORK))

from medium_transform_grid import (  # noqa: E402
    ACCOUNT_VALUE,
    CURRENT_VALUES,
    START,
    load,
    metrics,
    orders,
    sim,
    weights,
)
from nbis_storage_tilt_grid import BASE_ARGS, active_masks, overlay_weights  # noqa: E402


SMCI_CURRENT_WEIGHT = CURRENT_VALUES["SMCI"] / ACCOUNT_VALUE
SMCI_FLOORS = [0.0, 0.025, SMCI_CURRENT_WEIGHT, 0.05, 0.075, 0.10, 0.15, 0.20]
POLICIES = ["trend_gated", "tradable"]
FUNDING_ORDER = ["STX", "BIL", "AMD", "GEV", "NVDA", "MU", "SNDK", "NBIS"]


def apply_smci_floor(
    base: pd.DataFrame,
    trend_active: pd.DataFrame,
    tradable: pd.DataFrame,
    floor: float,
    policy: str,
) -> pd.DataFrame:
    columns = list(base.columns)
    column_index = {name: idx for idx, name in enumerate(columns)}
    active_source = trend_active if policy == "trend_gated" else tradable
    smci_active = active_source.reindex(base.index)["SMCI"].fillna(False).to_numpy(dtype=bool)
    arr = base.to_numpy(dtype=float, copy=True)
    smci_idx = column_index["SMCI"]
    bil_idx = column_index["BIL"]

    for pos in range(arr.shape[0]):
        if not smci_active[pos] or arr[pos, smci_idx] >= floor:
            continue
        need = floor - arr[pos, smci_idx]
        remaining = need
        for name in FUNDING_ORDER:
            if remaining <= 0:
                break
            fund_idx = column_index[name]
            take = min(remaining, max(arr[pos, fund_idx], 0))
            arr[pos, fund_idx] -= take
            remaining -= take
        arr[pos, smci_idx] += need - remaining
        arr[pos, :] = np.clip(arr[pos, :], 0, None)
        arr[pos, bil_idx] += 1.0 - float(arr[pos, :].sum())

    return pd.DataFrame(arr, index=base.index, columns=columns)


def live_order_sheet_with_dram(
    historical_sheet: pd.DataFrame,
    strategy_id: str,
) -> pd.DataFrame:
    rows: list[dict[str, float | str]] = []
    sndk_target = float(historical_sheet.loc[historical_sheet["ticker"] == "SNDK", "target_value"].iloc[0])
    dram_current = CURRENT_VALUES["DRAM"]
    for _, row in historical_sheet.iterrows():
        item = dict(row)
        ticker = str(item["ticker"])
        if ticker == "SNDK":
            continue
        if ticker == "DRAM":
            continue
        item["strategy_id"] = strategy_id
        rows.append(item)

    dram_price = CURRENT_VALUES["DRAM"] / 300.01
    dram_trade = sndk_target - dram_current
    rows.append(
        {
            "strategy_id": strategy_id,
            "ticker": "DRAM",
            "current_value": dram_current,
            "target_value": sndk_target,
            "trade_dollars": dram_trade,
            "price": dram_price,
            "approx_shares": dram_trade / dram_price,
            "target_weight": sndk_target / ACCOUNT_VALUE,
        }
    )
    out = pd.DataFrame(rows)
    out["target_weight"] = out["target_value"] / ACCOUNT_VALUE
    return out.sort_values("target_value", ascending=False)


def report(
    results: pd.DataFrame,
    selected: pd.Series,
    best: pd.Series,
    live_sheet: pd.DataFrame,
    chart: Path,
) -> str:
    table = results.sort_values(["cagr", "sharpe"], ascending=False).copy()
    cols = [
        "strategy_id",
        "cagr",
        "sharpe",
        "max_drawdown",
        "worst_12m",
        "turnover",
        "current_smci_weight",
        "current_stx_weight",
        "current_bil_weight",
    ]
    lines = [
        "# SMCI Keep Backtest",
        "",
        "Date: 2026-07-01",
        "",
        "## Question",
        "",
        "The user wants to keep SMCI. This tests SMCI as an explicit floor layered on top of the aggressive NBIS + storage-cap strategy.",
        "",
        "## Method",
        "",
        "- Base: aggressive NBIS/storage strategy from `NBIS_STORAGE_TILT.md`.",
        "- SMCI floors tested: 0%, 2.5%, current account weight, 5%, 7.5%, 10%, 15%, 20%.",
        "- Funding order: remove STX first, then BIL/cash, then smaller AI positions if needed.",
        "- Historical backtest still uses SNDK as the memory-stock proxy because DRAM ETF history is too short for a real long backtest.",
        "- Live order sheet maps the SNDK slot to the user's existing DRAM ETF position.",
        "",
        "## Results",
        "",
        f"- No-SMCI baseline: CAGR 55.9%, Sharpe 1.67, MaxDD -31.2%.",
        f"- Current-size SMCI floor: `{selected.strategy_id}`: CAGR {selected.cagr * 100:.1f}%, Sharpe {selected.sharpe:.2f}, MaxDD {selected.max_drawdown * 100:.1f}%.",
        f"- Best raw SMCI floor: `{best.strategy_id}`: CAGR {best.cagr * 100:.1f}%, Sharpe {best.sharpe:.2f}, MaxDD {best.max_drawdown * 100:.1f}%.",
        "",
        "## Full Grid",
        "",
        table[cols].to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Live Order Sheet",
        "",
        live_sheet.to_markdown(index=False, floatfmt=".2f"),
        "",
        "## Interpretation",
        "",
        "Keeping the current SMCI position did not hurt the backtest. It slightly improved CAGR and max drawdown versus the no-SMCI aggressive baseline. A 7.5%-10% SMCI floor had the highest raw CAGR in this specific test, but that is a bigger single-company execution/compliance bet.",
        "",
        "My practical choice is to keep SMCI at the current roughly 3% account weight, remove STX, and keep DRAM as the memory/HBM basket instead of adding SNDK.",
        "",
        f"Chart: `{chart.name}`",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    close, open_, fundamentals = load()
    base = weights(close, fundamentals, **BASE_ARGS)
    trend_active, tradable = active_masks(close)
    aggressive = overlay_weights(base, trend_active, tradable, 0.25, 0.30, 1.0, "tradable")
    rows: list[dict[str, float | str]] = []
    cache: dict[str, pd.DataFrame] = {}

    for policy in POLICIES:
        for floor in SMCI_FLOORS:
            w = apply_smci_floor(aggressive, trend_active, tradable, floor, policy)
            daily, turn = sim(close, open_, w, "close")
            latest = w.iloc[-1]
            sid = f"smci_floor={floor:.4f}|policy={policy}|on_aggressive_nbis_storage|close"
            rows.append(
                {
                    "strategy_id": sid,
                    "smci_floor": floor,
                    "policy": policy,
                    **metrics(daily, turn),
                    "current_smci_weight": float(latest["SMCI"]),
                    "current_stx_weight": float(latest["STX"]),
                    "current_bil_weight": float(latest["BIL"]),
                    "current_nbis_weight": float(latest["NBIS"]),
                    "current_storage_weight": float(latest[["MU", "SNDK", "STX"]].sum()),
                }
            )
            cache[sid] = w

    results = pd.DataFrame(rows)
    selected_sid = (
        f"smci_floor={SMCI_CURRENT_WEIGHT:.4f}|"
        "policy=tradable|on_aggressive_nbis_storage|close"
    )
    selected = results.loc[results["strategy_id"] == selected_sid].iloc[0]
    best = results.sort_values(["cagr", "sharpe"], ascending=False).iloc[0]
    selected_weights = cache[selected_sid]
    historical_sheet = orders(selected_weights, close, selected_sid)
    historical_sheet["target_weight"] = historical_sheet["target_value"] / ACCOUNT_VALUE
    live_sheet = live_order_sheet_with_dram(
        historical_sheet,
        "aggressive_25_nbis_30_DRAM_keep_SMCI_no_STX",
    )

    results.sort_values(["cagr", "sharpe"], ascending=False).to_csv(
        OUT / "smci_keep_backtest_results.csv",
        index=False,
    )
    historical_sheet.to_csv(OUT / "smci_keep_historical_proxy_order_sheet.csv", index=False)
    live_sheet.to_csv(OUT / "smci_keep_live_order_sheet.csv", index=False)
    selected_weights.iloc[-1].sort_values(ascending=False).rename("weight").to_csv(
        OUT / "smci_keep_backtest_weights.csv"
    )

    fig, ax = plt.subplots(figsize=(10, 6), dpi=160)
    for label, sid in {
        "no SMCI": "smci_floor=0.0000|policy=tradable|on_aggressive_nbis_storage|close",
        "keep current SMCI": selected_sid,
        "best raw SMCI": str(best.strategy_id),
    }.items():
        daily, _ = sim(close, open_, cache[sid], "close")
        ax.plot((1 + daily.loc[START:]).cumprod(), label=label)
    ax.set_yscale("log")
    ax.set_title("SMCI Floor Overlay Backtest")
    ax.set_ylabel("Log scale wealth, $1 initial")
    ax.grid(True, alpha=0.25)
    ax.legend()
    chart = OUT / "smci_keep_backtest_chart.png"
    fig.savefig(chart, bbox_inches="tight")
    (OUT / "SMCI_KEEP_BACKTEST.md").write_text(report(results, selected, best, live_sheet, chart))


if __name__ == "__main__":
    main()
