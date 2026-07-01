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
    AI_SLEEVE,
    CURRENT_VALUES,
    START,
    UNIVERSE,
    load,
    metrics,
    orders,
    sim,
    weights,
)


BASE_ARGS = {
    "size_t": "sqrt_raw_cap",
    "earn_t": "square",
    "mom_power": 1.5,
    "top_n": 7,
    "cadence": "weekly",
}
STORAGE_NAMES = ["MU", "SNDK", "STX"]
NBIS_FLOORS = [0.0, 0.05, 0.075, 0.10, 0.125, 0.15, 0.20, 0.25]
STORAGE_CAPS = [0.30, 0.35, 0.40, 0.45, 0.50, 0.55, AI_SLEEVE]
NBIS_REDIRECTS = [0.0, 0.25, 0.50, 0.75, 1.0]
POLICIES = ["trend_gated", "tradable"]


def active_masks(close: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    px = close[UNIVERSE].dropna(how="all")
    has_history = px.rolling(126).count().ge(126)
    basket = (1 + px.pct_change().mean(axis=1).fillna(0)).cumprod()
    trend = (px > px.rolling(100).mean()) & has_history
    trend = trend.mul(basket > basket.rolling(100).mean(), axis=0)
    return trend.reindex(close.index).fillna(False), has_history.reindex(close.index).fillna(False)


def take_weight(row: pd.Series, names: list[str], amount: float) -> float:
    available = row.reindex(names).fillna(0).clip(lower=0)
    total = float(available.sum())
    take = min(amount, total)
    if take > 0 and total > 0:
        row.loc[available.index] -= take * available / total
    return amount - take


def add_weight(row: pd.Series, names: list[str], amount: float) -> None:
    if amount <= 0:
        return
    available = row.reindex(names).fillna(0).clip(lower=0)
    total = float(available.sum())
    if total > 0:
        row.loc[available.index] += amount * available / total
    else:
        row.loc["BIL"] += amount


def apply_floor(row: pd.Series, nbis_floor: float, nbis_active: bool) -> None:
    if not nbis_active or nbis_floor <= row.get("NBIS", 0):
        return
    needed = nbis_floor - float(row.get("NBIS", 0))
    storage = [name for name in STORAGE_NAMES if name in row.index]
    non_storage_ai = [
        name for name in UNIVERSE if name not in STORAGE_NAMES and name != "NBIS" and name in row.index
    ]
    remaining = take_weight(row, storage, needed)
    remaining = take_weight(row, non_storage_ai, remaining)
    if remaining > 0:
        remaining = take_weight(row, ["BIL"], remaining)
    row.loc["NBIS"] += needed - remaining


def apply_storage_cap(
    row: pd.Series,
    storage_cap: float,
    nbis_redirect: float,
    nbis_active: bool,
) -> None:
    storage = [name for name in STORAGE_NAMES if name in row.index]
    storage_weight = float(row.reindex(storage).fillna(0).clip(lower=0).sum())
    if storage_weight <= storage_cap:
        return
    excess = storage_weight - storage_cap
    row.loc[storage] *= storage_cap / storage_weight
    nbis_add = excess * nbis_redirect if nbis_active else 0
    row.loc["NBIS"] += nbis_add
    remaining = excess - nbis_add
    recipients = [
        name
        for name in UNIVERSE
        if name not in STORAGE_NAMES and name != "NBIS" and name in row.index and row.loc[name] > 0
    ]
    add_weight(row, recipients, remaining)


def overlay_weights(
    base: pd.DataFrame,
    trend_active: pd.DataFrame,
    tradable: pd.DataFrame,
    nbis_floor: float,
    storage_cap: float,
    nbis_redirect: float,
    policy: str,
) -> pd.DataFrame:
    columns = list(base.columns)
    index_by_name = {name: i for i, name in enumerate(columns)}
    storage_idx = [index_by_name[name] for name in STORAGE_NAMES if name in index_by_name]
    non_storage_ai_idx = [
        index_by_name[name]
        for name in UNIVERSE
        if name not in STORAGE_NAMES and name != "NBIS" and name in index_by_name
    ]
    nbis_idx = index_by_name["NBIS"]
    bil_idx = index_by_name["BIL"]
    active_source = trend_active if policy == "trend_gated" else tradable
    active = active_source.reindex(base.index)["NBIS"].fillna(False).to_numpy(dtype=bool)
    arr = base.to_numpy(dtype=float, copy=True)

    def take_from(row: np.ndarray, idx: list[int], amount: float) -> float:
        if amount <= 0 or not idx:
            return amount
        available = np.clip(row[idx], 0, None)
        total = float(available.sum())
        take = min(amount, total)
        if take > 0 and total > 0:
            row[idx] -= take * available / total
        return amount - take

    def add_to(row: np.ndarray, idx: list[int], amount: float) -> None:
        if amount <= 0:
            return
        available = np.clip(row[idx], 0, None) if idx else np.array([])
        total = float(available.sum())
        if total > 0:
            row[idx] += amount * available / total
        else:
            row[bil_idx] += amount

    for pos in range(arr.shape[0]):
        row = arr[pos]
        nbis_active = bool(active[pos])
        if nbis_active and nbis_floor > row[nbis_idx]:
            needed = nbis_floor - row[nbis_idx]
            remaining = take_from(row, storage_idx, needed)
            remaining = take_from(row, non_storage_ai_idx, remaining)
            remaining = take_from(row, [bil_idx], remaining)
            row[nbis_idx] += needed - remaining

        storage_weight = float(np.clip(row[storage_idx], 0, None).sum())
        if storage_weight > storage_cap:
            excess = storage_weight - storage_cap
            row[storage_idx] *= storage_cap / storage_weight
            nbis_add = excess * nbis_redirect if nbis_active else 0
            row[nbis_idx] += nbis_add
            recipients = [idx for idx in non_storage_ai_idx if row[idx] > 0]
            add_to(row, recipients, excess - nbis_add)

        row[:] = np.clip(row, 0, None)
        row[bil_idx] += 1.0 - float(row.sum())

    return pd.DataFrame(arr, index=base.index, columns=columns)


def describe_current(w: pd.DataFrame) -> dict[str, float]:
    latest = w.iloc[-1]
    return {
        "current_nbis_weight": float(latest.get("NBIS", 0)),
        "current_storage_weight": float(latest.reindex(STORAGE_NAMES).fillna(0).sum()),
        "current_ai_weight": float(latest.reindex(UNIVERSE).fillna(0).sum()),
    }


def order_sheet(strategy_id: str, w: pd.DataFrame, close: pd.DataFrame) -> pd.DataFrame:
    sheet = orders(w, close, strategy_id)
    sheet["target_weight"] = sheet["target_value"] / ACCOUNT_VALUE
    return sheet


def plot_results(res: pd.DataFrame, curves: dict[str, pd.Series]) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(15, 6), dpi=160)
    sc = axes[0].scatter(
        res["max_drawdown"].abs() * 100,
        res["cagr"] * 100,
        c=res["current_nbis_weight"] * 100,
        s=18,
        cmap="plasma",
        alpha=0.65,
    )
    for label in ["baseline", "strict", "selected", "best_raw"]:
        match = res.loc[res["label"].str.contains(label, regex=False)]
        if match.empty:
            continue
        row = match.iloc[0]
        axes[0].scatter(
            abs(row["max_drawdown"]) * 100,
            row["cagr"] * 100,
            s=170,
            edgecolor="white",
            linewidth=1.2,
            label=label,
        )
    axes[0].set_title("NBIS Floor + Storage Cap Grid")
    axes[0].set_xlabel("10-year max drawdown")
    axes[0].set_ylabel("10-year CAGR")
    axes[0].grid(True, alpha=0.25)
    axes[0].legend()
    fig.colorbar(sc, ax=axes[0], label="Current NBIS weight")

    for label, curve in curves.items():
        axes[1].plot(curve.index, curve, label=label)
    axes[1].set_yscale("log")
    axes[1].set_title("Equity Curve, $1 Initial")
    axes[1].set_ylabel("Log scale wealth")
    axes[1].grid(True, alpha=0.25)
    axes[1].legend()
    chart = OUT / "nbis_storage_tilt_chart.png"
    fig.savefig(chart, bbox_inches="tight")
    return chart


def build_report(
    res: pd.DataFrame,
    baseline: pd.Series,
    strict: pd.Series,
    selected: pd.Series,
    best_raw: pd.Series,
    selected_orders: pd.DataFrame,
    chart: Path,
) -> str:
    top = res.sort_values(["cagr", "sharpe"], ascending=False).head(15).copy()
    cols = [
        "strategy_id",
        "cagr",
        "sharpe",
        "max_drawdown",
        "worst_12m",
        "turnover",
        "current_nbis_weight",
        "current_storage_weight",
    ]
    for col in cols[1:]:
        top[col] = top[col].astype(float)
    selected_weights = pd.read_csv(OUT / "nbis_storage_selected_weights.csv")
    lines = [
        "# NBIS Conviction And Storage Cap Grid",
        "",
        "Date: 2026-07-01",
        "",
        "## Question",
        "",
        "The previous optimizer placed very high weight in memory/storage names and very low weight in NBIS. This run treats NBIS conviction and storage concentration as explicit hyperparameters.",
        "",
        "## Grid Tested",
        "",
        "- Base strategy: sqrt raw market-cap, squared earnings score, 6-month momentum^1.5, top 7, weekly rebalance, close-to-close returns.",
        "- NBIS floor: 0%, 5%, 7.5%, 10%, 12.5%, 15%, 20%, 25% of the whole account.",
        "- Storage cap: 30%, 35%, 40%, 45%, 50%, 55%, or uncapped 70% of the whole account across MU/SNDK/STX.",
        "- NBIS activation policy: trend-gated or tradable-with-history.",
        "- Storage excess redirect: 0%, 25%, 50%, 75%, or 100% of storage-cap excess directed to NBIS.",
        "",
        "## Key Results",
        "",
        f"- Baseline robust optimizer: CAGR {baseline.cagr * 100:.1f}%, Sharpe {baseline.sharpe:.2f}, MaxDD {baseline.max_drawdown * 100:.1f}%, current NBIS {baseline.current_nbis_weight * 100:.1f}%, current storage {baseline.current_storage_weight * 100:.1f}%.",
        f"- Strict audited NBIS tilt: `{strict.strategy_id}`: CAGR {strict.cagr * 100:.1f}%, Sharpe {strict.sharpe:.2f}, MaxDD {strict.max_drawdown * 100:.1f}%, current NBIS {strict.current_nbis_weight * 100:.1f}%, current storage {strict.current_storage_weight * 100:.1f}%.",
        f"- Best raw overlay: `{best_raw.strategy_id}`: CAGR {best_raw.cagr * 100:.1f}%, Sharpe {best_raw.sharpe:.2f}, MaxDD {best_raw.max_drawdown * 100:.1f}%, current NBIS {best_raw.current_nbis_weight * 100:.1f}%, current storage {best_raw.current_storage_weight * 100:.1f}%.",
        f"- Selected conviction overlay: `{selected.strategy_id}`: CAGR {selected.cagr * 100:.1f}%, Sharpe {selected.sharpe:.2f}, MaxDD {selected.max_drawdown * 100:.1f}%, current NBIS {selected.current_nbis_weight * 100:.1f}%, current storage {selected.current_storage_weight * 100:.1f}%.",
        "",
        "## NBIS Data Caveat",
        "",
        "NBIS clean price history in this data starts on 2024-10-21, when Nasdaq trading resumed under the Nebius name. So the NBIS overlay is not a pure 10-year NBIS proof. It is a current-conviction overlay tested inside a 10-year framework.",
        "",
        "## Top 15 By CAGR",
        "",
        top[cols].to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Selected Current Weights",
        "",
        selected_weights.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Selected Order Sheet",
        "",
        selected_orders.to_markdown(index=False, floatfmt=".2f"),
        "",
        "## Interpretation",
        "",
        "The storage-heavy result is not a generic AI result. It is mostly a memory-cycle result. NBIS can be made a real position without breaking the historical backtest, but the evidence quality is lower than for long-history names because NBIS has only clean post-resumption trading history.",
        "",
        "My practical preference for a return-seeking account is the selected conviction overlay if you really believe the NBIS thesis. The stricter audited version is the 10% NBIS / 45% storage-cap rule. The aggressive version is the 25%+ NBIS / 30% storage-cap rule.",
        "",
        f"Chart: `{chart.name}`",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    close, open_, fundamentals = load()
    base = weights(close, fundamentals, **BASE_ARGS)
    trend_active, tradable = active_masks(close)
    rows: list[dict[str, float | str]] = []
    weight_cache: dict[str, pd.DataFrame] = {}

    for policy in POLICIES:
        for floor in NBIS_FLOORS:
            for cap in STORAGE_CAPS:
                for redirect in NBIS_REDIRECTS:
                    w = overlay_weights(base, trend_active, tradable, floor, cap, redirect, policy)
                    daily, turn = sim(close, open_, w, "close")
                    sid = (
                        f"nbis_floor={floor:.3f}|storage_cap={cap:.3f}|"
                        f"policy={policy}|storage_excess_to_nbis={redirect:.2f}|close"
                    )
                    rows.append(
                        {
                            "strategy_id": sid,
                            "nbis_floor": floor,
                            "storage_cap": cap,
                            "policy": policy,
                            "storage_excess_to_nbis": redirect,
                            **metrics(daily, turn),
                            **describe_current(w),
                        }
                    )
                    weight_cache[sid] = w

    res = pd.DataFrame(rows)
    baseline_sid = (
        "nbis_floor=0.000|storage_cap=0.700|"
        "policy=trend_gated|storage_excess_to_nbis=0.00|close"
    )
    strict_sid = (
        "nbis_floor=0.100|storage_cap=0.450|"
        "policy=trend_gated|storage_excess_to_nbis=0.00|close"
    )
    res["label"] = ""

    def mark(strategy_id: str, label: str) -> None:
        mask = res["strategy_id"] == strategy_id
        res.loc[mask, "label"] = res.loc[mask, "label"].apply(
            lambda existing: label if existing == "" else f"{existing};{label}"
        )

    mark(baseline_sid, "baseline")
    mark(strict_sid, "strict")

    eligible = res[
        (res["nbis_floor"] >= 0.10)
        & (res["storage_cap"] <= 0.45)
        & (res["current_nbis_weight"] >= 0.10)
        & (res["current_storage_weight"] <= 0.45)
        & (res["turnover"] <= 18)
        & (res["max_drawdown"] >= -0.36)
    ]
    selected = eligible.sort_values(["cagr", "sharpe"], ascending=False).iloc[0]
    best_raw = res.sort_values(["cagr", "sharpe"], ascending=False).iloc[0]
    baseline = res.loc[res["strategy_id"] == baseline_sid].iloc[0]
    strict = res.loc[res["strategy_id"] == strict_sid].iloc[0]
    mark(str(selected.strategy_id), "selected")
    mark(str(best_raw.strategy_id), "best_raw")

    selected_w = weight_cache[str(selected.strategy_id)]
    strict_w = weight_cache[strict_sid]
    best_w = weight_cache[str(best_raw.strategy_id)]
    baseline_w = weight_cache[baseline_sid]
    strict_orders = order_sheet(strict_sid, strict_w, close)
    selected_orders = order_sheet(str(selected.strategy_id), selected_w, close)
    strict_orders.to_csv(OUT / "nbis_storage_strict_order_sheet.csv", index=False)
    selected_orders.to_csv(OUT / "nbis_storage_selected_order_sheet.csv", index=False)
    strict_w.iloc[-1].sort_values(ascending=False).rename("weight").to_csv(
        OUT / "nbis_storage_strict_weights.csv"
    )
    selected_w.iloc[-1].sort_values(ascending=False).rename("weight").to_csv(
        OUT / "nbis_storage_selected_weights.csv"
    )
    res.sort_values(["cagr", "sharpe"], ascending=False).to_csv(
        OUT / "nbis_storage_tilt_results.csv", index=False
    )

    curves = {}
    for label, w in {
        "baseline": baseline_w,
        "strict audited NBIS tilt": strict_w,
        "selected NBIS/storage overlay": selected_w,
        "best raw overlay": best_w,
    }.items():
        daily, _ = sim(close, open_, w, "close")
        curves[label] = (1 + daily.loc[START:]).cumprod()
    qqq_curve = (1 + close["QQQ"].pct_change().fillna(0).loc[START:]).cumprod()
    curves["QQQ buy-and-hold"] = qqq_curve
    chart = plot_results(res, curves)
    report = build_report(res, baseline, strict, selected, best_raw, selected_orders, chart)
    (OUT / "NBIS_STORAGE_TILT.md").write_text(report)


if __name__ == "__main__":
    main()
