from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work"
OUT = ROOT / "outputs"
sys.path.append(str(WORK))

from exit_rule_comparison import add_gold_data  # noqa: E402
from medium_transform_grid import ACCOUNT_VALUE, START, TRADING_DAYS, UNIVERSE, load  # noqa: E402
from nbis_redirect_sensitivity import build_weights  # noqa: E402


@dataclass(frozen=True)
class Policy:
    name: str
    kind: str
    weeks: int = 0
    now_fraction: float = 0.0
    dip: float = 0.0
    timeout_days: int = 0
    ma_days: int = 0


POLICIES = [
    Policy("Lump sum now", "lump"),
    Policy("DCA 3m", "dca", weeks=13),
    Policy("DCA 6m", "dca", weeks=26),
    Policy("DCA 12m", "dca", weeks=52),
    Policy("50% now + DCA 6m", "hybrid_dca", weeks=26, now_fraction=0.50),
    Policy("70% now + buy 10% dip/6m", "hybrid_dip", now_fraction=0.70, dip=0.10, timeout_days=126),
    Policy("Wait 5% dip/3m", "wait_dip", dip=0.05, timeout_days=63),
    Policy("Wait 10% dip/6m", "wait_dip", dip=0.10, timeout_days=126),
    Policy("Wait 20% dip/12m", "wait_dip", dip=0.20, timeout_days=252),
    Policy("Trend entry 100d", "trend_above_ma", ma_days=100, timeout_days=126),
    Policy("Buy lower: below 100d/6m", "wait_below_ma", ma_days=100, timeout_days=126),
]

HORIZONS = {
    "1y": 252,
    "3y": 756,
    "5y": 1260,
}


def normalize(weights: pd.Series) -> pd.Series:
    out = weights.fillna(0.0).clip(lower=0.0)
    total = float(out.sum())
    if total <= 0:
        raise ValueError("Weight sum is zero")
    return out / total


def portfolio_index(close: pd.DataFrame, weights: pd.Series) -> pd.Series:
    weights = normalize(weights)
    prices = close[weights.index].ffill().dropna()
    relatives = prices.div(prices.iloc[0])
    return relatives.mul(weights, axis=1).sum(axis=1)


def full_history_weights(close: pd.DataFrame) -> tuple[pd.Series, list[str]]:
    prices = close[UNIVERSE].loc[START:].ffill()
    tickers = [ticker for ticker in UNIVERSE if pd.notna(prices[ticker].iloc[0])]
    return pd.Series(1.0, index=tickers), tickers


def current_target_weights(close: pd.DataFrame, fundamentals: pd.DataFrame) -> pd.Series:
    target = build_weights(close, fundamentals, 0.15, 0.50, "weekly").iloc[-1]
    target = target[target > 0].copy()
    return normalize(target)


def simulate_entry(
    idx: pd.Series,
    ma: pd.Series,
    start_pos: int,
    horizon: int,
    policy: Policy,
) -> pd.Series:
    path = idx.iloc[start_pos : start_pos + horizon + 1]
    cash = 1.0
    shares = 0.0
    values = []
    tranche_count = max(policy.weeks, 1)
    high = float(path.iloc[0])

    for absolute_pos, price in zip(range(start_pos, start_pos + len(path)), path):
        elapsed = absolute_pos - start_pos
        price = float(price)
        high = max(high, price)
        amount = 0.0

        if policy.kind == "lump":
            amount = 1.0 if elapsed == 0 else 0.0
        elif policy.kind == "dca":
            if elapsed % 5 == 0 and elapsed // 5 < tranche_count:
                amount = 1.0 / tranche_count
        elif policy.kind == "hybrid_dca":
            if elapsed == 0:
                amount = policy.now_fraction
            elif elapsed % 5 == 0 and elapsed // 5 < tranche_count:
                amount = (1.0 - policy.now_fraction) / tranche_count
        elif policy.kind in {"wait_dip", "hybrid_dip"}:
            drawdown = price / high - 1.0
            trigger = drawdown <= -policy.dip or elapsed >= policy.timeout_days
            if policy.kind == "hybrid_dip":
                if elapsed == 0:
                    amount = policy.now_fraction
                elif trigger:
                    amount = 1.0 - policy.now_fraction
            elif trigger:
                amount = 1.0
        elif policy.kind in {"trend_above_ma", "wait_below_ma"}:
            ma_value = float(ma.iloc[absolute_pos])
            has_ma = pd.notna(ma_value)
            above_ma = has_ma and price > ma_value
            below_ma = has_ma and price < ma_value
            timed_out = elapsed >= policy.timeout_days
            if policy.kind == "trend_above_ma" and (above_ma or timed_out):
                amount = 1.0
            elif policy.kind == "wait_below_ma" and (below_ma or timed_out):
                amount = 1.0
        else:
            raise ValueError(policy.kind)

        amount = min(cash, amount)
        if amount > 0 and price > 0:
            shares += amount / price
            cash -= amount
        values.append(cash + shares * price)

    if cash > 1e-12:
        final_price = float(path.iloc[-1])
        shares += cash / final_price
        cash = 0.0
        values[-1] = cash + shares * final_price

    return pd.Series(values, index=path.index)


def max_drawdown(curve: pd.Series) -> float:
    return float((curve / curve.cummax() - 1.0).min())


def rolling_results(idx: pd.Series, asset_name: str) -> pd.DataFrame:
    idx = idx.loc[START:].dropna()
    ma = idx.rolling(100).mean()
    rows = []
    for horizon_name, horizon in HORIZONS.items():
        if len(idx) <= horizon:
            continue
        start_positions = range(0, len(idx) - horizon, 5)
        lump_values = {}
        for start_pos in start_positions:
            lump_curve = simulate_entry(idx, ma, start_pos, horizon, POLICIES[0])
            lump_values[start_pos] = float(lump_curve.iloc[-1])
        for policy in POLICIES:
            cagr_values = []
            maxdds = []
            wins = []
            end_values = []
            for start_pos in start_positions:
                curve = simulate_entry(idx, ma, start_pos, horizon, policy)
                end_value = float(curve.iloc[-1])
                end_values.append(end_value)
                cagr_values.append(end_value ** (TRADING_DAYS / horizon) - 1.0)
                maxdds.append(max_drawdown(curve))
                wins.append(end_value > lump_values[start_pos])
            rows.append(
                {
                    "asset": asset_name,
                    "horizon": horizon_name,
                    "policy": policy.name,
                    "samples": len(end_values),
                    "median_cagr": float(np.median(cagr_values)),
                    "mean_cagr": float(np.mean(cagr_values)),
                    "p10_cagr": float(np.quantile(cagr_values, 0.10)),
                    "worst_cagr": float(np.min(cagr_values)),
                    "median_max_drawdown": float(np.median(maxdds)),
                    "win_rate_vs_lump": float(np.mean(wins)),
                    "median_end_value": float(np.median(end_values) * ACCOUNT_VALUE),
                }
            )
    return pd.DataFrame(rows)


def single_window_results(idx: pd.Series, asset_name: str, start: str) -> pd.DataFrame:
    idx = idx.loc[start:].dropna()
    ma = idx.rolling(100).mean()
    horizon = len(idx) - 1
    rows = []
    lump_end = float(simulate_entry(idx, ma, 0, horizon, POLICIES[0]).iloc[-1])
    for policy in POLICIES:
        curve = simulate_entry(idx, ma, 0, horizon, policy)
        end_value = float(curve.iloc[-1])
        rows.append(
            {
                "asset": asset_name,
                "start": start,
                "horizon_days": horizon,
                "policy": policy.name,
                "cagr": end_value ** (TRADING_DAYS / horizon) - 1.0,
                "max_drawdown": max_drawdown(curve),
                "end_value": end_value * ACCOUNT_VALUE,
                "beats_lump": end_value > lump_end,
            }
        )
    return pd.DataFrame(rows)


def format_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def formatted_rollup(frame: pd.DataFrame, asset: str, horizon: str) -> pd.DataFrame:
    out = frame[(frame["asset"] == asset) & (frame["horizon"] == horizon)].copy()
    columns = [
        "policy",
        "median_cagr",
        "p10_cagr",
        "worst_cagr",
        "median_max_drawdown",
        "win_rate_vs_lump",
    ]
    out = out[columns]
    for col in columns[1:]:
        out[col] = out[col].map(format_percent)
    return out


def plot_policy_bars(results: pd.DataFrame, horizon: str, path: Path) -> None:
    policies = [policy.name for policy in POLICIES]
    fig, axes = plt.subplots(1, 2, figsize=(16, 7), dpi=160, sharey=True)
    for ax, asset in zip(axes, ["QQQ", "Full-history AI/semis"]):
        data = results[(results["asset"] == asset) & (results["horizon"] == horizon)]
        data = data.set_index("policy").reindex(policies)
        x = np.arange(len(policies))
        ax.bar(x, data["median_cagr"] * 100, label="median CAGR", color="#2563eb")
        ax.scatter(x, data["p10_cagr"] * 100, label="10th percentile", color="#dc2626", zorder=3)
        lump_median = float(data.loc["Lump sum now", "median_cagr"]) * 100
        ax.axhline(lump_median, color="black", lw=1, ls="--")
        ax.set_title(f"{asset}: {horizon} rolling starts")
        ax.set_xticks(x)
        ax.set_xticklabels(policies, rotation=45, ha="right")
        ax.grid(True, axis="y", alpha=0.25)
        ax.legend()
    axes[0].set_ylabel("Forward CAGR")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def plot_win_rates(results: pd.DataFrame, horizon: str, path: Path) -> None:
    policies = [policy.name for policy in POLICIES if policy.name != "Lump sum now"]
    fig, axes = plt.subplots(1, 2, figsize=(16, 6), dpi=160, sharey=True)
    for ax, asset in zip(axes, ["QQQ", "Full-history AI/semis"]):
        data = results[(results["asset"] == asset) & (results["horizon"] == horizon)]
        data = data.set_index("policy").reindex(policies)
        ax.bar(np.arange(len(policies)), data["win_rate_vs_lump"] * 100, color="#16a34a")
        ax.axhline(50, color="black", lw=1, ls="--")
        ax.set_title(f"{asset}: win rate vs lump sum ({horizon})")
        ax.set_xticks(np.arange(len(policies)))
        ax.set_xticklabels(policies, rotation=45, ha="right")
        ax.grid(True, axis="y", alpha=0.25)
    axes[0].set_ylabel("% of rolling starts beating lump sum")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def plot_single_window(single: pd.DataFrame, path: Path) -> None:
    data = single[single["asset"] == "Current target basket"].copy()
    data = data.set_index("policy").reindex([policy.name for policy in POLICIES])
    fig, ax = plt.subplots(figsize=(13, 6), dpi=160)
    ax.bar(np.arange(len(data)), data["end_value"] / 1_000_000, color="#f97316")
    lump = float(data.loc["Lump sum now", "end_value"]) / 1_000_000
    ax.axhline(lump, color="black", lw=1, ls="--", label="lump sum")
    ax.set_title("Current Target Basket: Entry Timing Since Common Start")
    ax.set_ylabel("End value, $M")
    ax.set_xticks(np.arange(len(data)))
    ax.set_xticklabels(data.index, rotation=45, ha="right")
    ax.grid(True, axis="y", alpha=0.25)
    ax.legend()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    close, _, fundamentals = load()
    close, _ = add_gold_data(close, close)

    qqq_index = close["QQQ"] / close["QQQ"].dropna().iloc[0]
    full_weights, full_tickers = full_history_weights(close)
    full_index = portfolio_index(close, full_weights)
    target = current_target_weights(close, fundamentals)
    target_start = max(close[ticker].first_valid_index() for ticker in target.index)
    current_index = portfolio_index(close, target)
    target_start_text = str(target_start.date())

    rolling = pd.concat(
        [
            rolling_results(qqq_index, "QQQ"),
            rolling_results(full_index, "Full-history AI/semis"),
        ],
        ignore_index=True,
    )
    single = single_window_results(current_index, "Current target basket", target_start_text)

    OUT.mkdir(exist_ok=True)
    rolling.to_csv(OUT / "buy_hold_entry_timing_rolling_results.csv", index=False)
    single.to_csv(OUT / "buy_hold_entry_timing_current_basket.csv", index=False)

    bar_chart = OUT / "buy_hold_entry_timing_3y_bars.png"
    win_chart = OUT / "buy_hold_entry_timing_3y_win_rates.png"
    current_chart = OUT / "buy_hold_entry_timing_current_basket.png"
    plot_policy_bars(rolling, "3y", bar_chart)
    plot_win_rates(rolling, "3y", win_chart)
    plot_single_window(single, current_chart)

    qqq_3y = formatted_rollup(rolling, "QQQ", "3y")
    ai_3y = formatted_rollup(rolling, "Full-history AI/semis", "3y")
    current_display = single.copy()
    current_display["cagr"] = current_display["cagr"].map(format_percent)
    current_display["max_drawdown"] = current_display["max_drawdown"].map(format_percent)
    current_display["end_value"] = current_display["end_value"].map(
        lambda x: f"${x / 1_000_000:.2f}M"
    )
    current_display = current_display[["policy", "cagr", "max_drawdown", "end_value", "beats_lump"]]

    lines = [
        "# Buy-and-Hold Entry Timing Tests",
        "",
        "Date: 2026-07-01",
        "",
        "## Method",
        "",
        "- Tests entry timing for buy-and-hold, not the weekly strategy.",
        "- Rolling tests use every fifth trading day as a hypothetical start date.",
        "- Full-history AI/semis bracket includes only names with data at 2016-07-01: "
        f"`{', '.join(full_tickers)}`.",
        f"- Current target basket starts at `{target_start_text}` because "
        "NBIS/GEV/SNDK history is short.",
        "- Cash waiting earns 0% in these tests. That is conservative for DCA/waiting rules.",
        "- A wait rule that never triggers deploys at its timeout, so no "
        "strategy hides in cash forever.",
        "",
        "## 3-Year Rolling Starts: QQQ",
        "",
        qqq_3y.to_markdown(index=False),
        "",
        "## 3-Year Rolling Starts: Full-History AI/Semis",
        "",
        ai_3y.to_markdown(index=False),
        "",
        "## Current Target Basket: Single Common Window",
        "",
        current_display.to_markdown(index=False),
        "",
        "## Interpretation",
        "",
        "- Lump-sum buy-and-hold is the hardest entry rule to beat in upward-drifting assets.",
        "- DCA and waiting rules can reduce regret/drawdown, but they usually lose median CAGR.",
        "- Waiting for a 10-20% dip is especially costly when the dip does not arrive quickly.",
        "- If choosing buy-and-hold for the current AI basket, the model "
        "evidence favors buying now or mostly now, not waiting for a perfect dip.",
        "- The honest reason to use band strategy instead of buy-and-hold is "
        "not higher after-tax return versus every AI basket; it is a rule-based "
        "attempt to cap drawdown/regime risk.",
        "",
        "## Charts",
        "",
        f"- `{bar_chart.name}`",
        f"- `{win_chart.name}`",
        f"- `{current_chart.name}`",
    ]
    (OUT / "BUY_HOLD_ENTRY_TIMING.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
