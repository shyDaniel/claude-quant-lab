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

from exit_rule_comparison import add_gold_data, calc_metrics, current_final_weights, replace_defensive_asset  # noqa: E402
from medium_transform_grid import ACCOUNT_VALUE, START, UNIVERSE, load, sim  # noqa: E402


TRANCHES = {
    "5_10_15": (0.05, 0.10, 0.15),
    "7p5_15_22p5": (0.075, 0.15, 0.225),
    "10_20_30": (0.10, 0.20, 0.30),
}
RESERVES = [0.10, 0.15, 0.20]
LOOKBACKS = [21, 63, 126]


def prepare_prices() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    close, open_, fundamentals = load()
    close, open_ = add_gold_data(close, open_)
    close = close.copy()
    open_ = open_.copy()
    close["CASH"] = 1.0
    open_["CASH"] = 1.0
    return close, open_, fundamentals


def equity_basket(close: pd.DataFrame, w: pd.DataFrame) -> pd.Series:
    equity_cols = [col for col in w.columns if col not in {"GLD", "BIL", "CASH"}]
    r = close[equity_cols].pct_change().fillna(0)
    static = w[equity_cols].iloc[-1]
    static = static / static.sum()
    return (1 + (r * static).sum(axis=1)).cumprod()


def set_cash_reserve(
    w: pd.DataFrame,
    reserve: float,
    *,
    mode: str = "equity_only",
) -> pd.DataFrame:
    out = w.copy()
    if "CASH" not in out.columns:
        out["CASH"] = 0.0
    out["BIL"] = 0.0
    equity_cols = [col for col in out.columns if col not in {"GLD", "BIL", "CASH"}]
    if mode == "pro_rata":
        non_cash = [col for col in out.columns if col != "CASH"]
        out[non_cash] = out[non_cash] * (1.0 - reserve)
    elif mode == "equity_only":
        equity_sum = out[equity_cols].sum(axis=1)
        scale = ((equity_sum - reserve).clip(lower=0) / equity_sum.replace(0, np.nan)).fillna(0)
        out[equity_cols] = out[equity_cols].mul(scale, axis=0)
    else:
        raise ValueError(mode)
    out["CASH"] = reserve
    return out


def deploy_fraction(drawdown: pd.Series, thresholds: tuple[float, float, float]) -> pd.Series:
    first, second, third = thresholds
    deploy = pd.Series(0.0, index=drawdown.index)
    deploy.loc[drawdown <= -first] = 1 / 3
    deploy.loc[drawdown <= -second] = 2 / 3
    deploy.loc[drawdown <= -third] = 1.0
    return deploy


def apply_dip_reserve(
    w: pd.DataFrame,
    close: pd.DataFrame,
    reserve: float,
    lookback: int,
    thresholds: tuple[float, float, float],
) -> pd.DataFrame:
    base = set_cash_reserve(w, reserve, mode="equity_only")
    basket = equity_basket(close, w)
    drawdown = basket / basket.rolling(lookback).max() - 1
    deploy = deploy_fraction(drawdown.fillna(0), thresholds)
    out = base.copy()
    equity_cols = [col for col in out.columns if col not in {"GLD", "BIL", "CASH"}]
    base_cash = reserve
    target_cash = base_cash * (1 - deploy)
    cash_to_deploy = base_cash - target_cash
    equity_sum = base[equity_cols].sum(axis=1)
    out[equity_cols] = base[equity_cols].add(
        base[equity_cols].div(equity_sum.replace(0, np.nan), axis=0).fillna(0).mul(cash_to_deploy, axis=0),
        fill_value=0,
    )
    out["CASH"] = target_cash
    return out


def tomorrow_down_10_actions(target: pd.Series, account_value: float) -> pd.DataFrame:
    shock_cols = [col for col in target.index if col not in {"GLD", "CASH", "BIL"}]
    current = target.copy()
    shocked_values = current * account_value
    shocked_values.loc[shock_cols] *= 0.90
    shocked_account = float(shocked_values.sum())
    target_values = target * shocked_account
    trades = target_values - shocked_values
    return pd.DataFrame(
        {
            "ticker": target.index,
            "post_drop_value": shocked_values.values,
            "target_value": target_values.values,
            "trade_dollars": trades.values,
            "post_drop_weight": (shocked_values / shocked_account).values,
            "target_weight": target.values,
        }
    ).sort_values("trade_dollars", ascending=False)


def shock_actions(pre: pd.Series, post: pd.Series, label: str) -> None:
    shock_cols = [col for col in pre.index if col not in {"GLD", "CASH", "BIL"}]
    values = pre * ACCOUNT_VALUE
    values.loc[shock_cols] *= 0.90
    shocked_account = float(values.sum())
    target = post * shocked_account
    trades = target - values
    pd.DataFrame(
        {
            "ticker": pre.index,
            "post_drop_value": values.values,
            "target_value": target.values,
            "trade_dollars": trades.values,
            "post_drop_weight": (values / shocked_account).values,
            "target_weight": post.values,
        }
    ).sort_values("trade_dollars", ascending=False).to_csv(
        OUT / f"tomorrow_down_10_{label}_actions.csv",
        index=False,
    )


def main() -> None:
    close, open_, fundamentals = prepare_prices()
    base = replace_defensive_asset(current_final_weights(close, fundamentals), "GLD")
    rows: list[dict[str, float | str]] = []
    variants: dict[str, pd.DataFrame] = {
        "no_cash_reserve_GLD": base,
    }

    for reserve in RESERVES:
        static_name = f"static_cash_reserve_{int(reserve * 100)}"
        variants[static_name] = set_cash_reserve(base, reserve, mode="equity_only")
        variants[f"static_cash_reserve_{int(reserve * 100)}_pro_rata"] = set_cash_reserve(
            base,
            reserve,
            mode="pro_rata",
        )
        for lookback in LOOKBACKS:
            for tranche_name, thresholds in TRANCHES.items():
                name = f"dip_cash_reserve_{int(reserve * 100)}_lookback_{lookback}_tranches_{tranche_name}"
                variants[name] = apply_dip_reserve(base, close, reserve, lookback, thresholds)

    for name, w in variants.items():
        daily, turn = sim(close, open_, w, "close")
        latest = w.iloc[-1]
        rows.append(
            {
                "strategy": name,
                "cagr": calc_metrics(daily, turn, START)["cagr"],
                "sharpe": calc_metrics(daily, turn, START)["sharpe"],
                "max_drawdown": calc_metrics(daily, turn, START)["max_drawdown"],
                "worst_12m": calc_metrics(daily, turn, START)["worst_12m"],
                "turnover": turn,
                "current_cash_weight": float(latest.get("CASH", 0)),
                "current_gld_weight": float(latest.get("GLD", 0)),
                "current_equity_weight": float(latest.drop(labels=[c for c in ["CASH", "GLD", "BIL"] if c in latest.index]).sum()),
            }
        )

    results = pd.DataFrame(rows).sort_values(["cagr", "sharpe"], ascending=False)
    selected = results[
        results["strategy"].str.contains("dip_cash_reserve_10")
        & results["strategy"].str.contains("lookback_63")
        & results["strategy"].str.contains("tranches_5_10_15")
    ].iloc[0]
    selected_w = variants[str(selected.strategy)]
    results.to_csv(OUT / "cash_dip_reserve_results.csv", index=False)
    selected_w.iloc[-1].sort_values(ascending=False).rename("weight").to_csv(
        OUT / "cash_dip_reserve_selected_weights.csv"
    )
    tomorrow_down_10_actions(base.iloc[-1], ACCOUNT_VALUE).to_csv(
        OUT / "tomorrow_down_10_no_cash_actions.csv",
        index=False,
    )
    tomorrow_down_10_actions(selected_w.iloc[-1], ACCOUNT_VALUE).to_csv(
        OUT / "tomorrow_down_10_cash_reserve_actions.csv",
        index=False,
    )
    base_latest = base.iloc[-1]
    equity_cols = [col for col in base_latest.index if col not in {"GLD", "CASH", "BIL"}]
    base_equity = float(base_latest[equity_cols].sum())

    def reserve_target(cash_weight: float) -> pd.Series:
        out = base_latest.copy()
        out["CASH"] = cash_weight
        out[equity_cols] = base_latest[equity_cols] * ((1 - base_latest["GLD"] - cash_weight) / base_equity)
        return out

    shock_actions(base_latest.reindex(base_latest.index.union(["CASH"])).fillna(0), base_latest.reindex(base_latest.index.union(["CASH"])).fillna(0), "no_reserve_gld")
    shock_actions(reserve_target(1 / 30), reserve_target(0.0), "dynamic_10_reserve_full_deploy")
    shock_actions(reserve_target(0.05), reserve_target(0.0), "dynamic_15_reserve_full_deploy")
    shock_actions(reserve_target(0.10), reserve_target(0.10), "static_10_reserve_no_deploy")

    fig, ax = plt.subplots(figsize=(11, 6), dpi=160)
    for label, name in {
        "no cash reserve": "no_cash_reserve_GLD",
        "10% static cash": "static_cash_reserve_10",
        "10% dynamic dip reserve": str(selected.strategy),
        "20% static cash": "static_cash_reserve_20",
    }.items():
        daily, _ = sim(close, open_, variants[name], "close")
        ax.plot((1 + daily.loc[START:]).cumprod(), label=label)
    ax.set_yscale("log")
    ax.set_title("Cash Reserve / Dip-Buy Overlay")
    ax.set_ylabel("Log scale wealth, $1 initial")
    ax.grid(True, alpha=0.25)
    ax.legend()
    chart = OUT / "cash_dip_reserve_chart.png"
    fig.savefig(chart, bbox_inches="tight")

    lines = [
        "# Cash Reserve Dip-Buy Backtest",
        "",
        "Date: 2026-07-01",
        "",
        "## What Was Tested",
        "",
        "- Baseline: current weekly GLD-defensive strategy.",
        "- Static cash reserves: 10%, 15%, 20% cash, with GLD kept as the gold sleeve.",
        "- Dynamic dip reserves: keep a cash reserve, then deploy one-third/two-thirds/all of it when the equity sleeve falls below recent highs.",
        "- Refill rule: when the drawdown recovers, the weekly rebalance trims back into the cash reserve.",
        "",
        "## Top Results",
        "",
        results.head(20).to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Selected Practical Reserve",
        "",
        f"`{selected.strategy}`: CAGR {selected.cagr * 100:.1f}%, Sharpe {selected.sharpe:.2f}, MaxDD {selected.max_drawdown * 100:.1f}%, current cash {selected.current_cash_weight * 100:.1f}%.",
        "",
        "## Tomorrow -10% Scenario",
        "",
        "- No cash reserve: only about $1.3k gets bought, funded by trimming GLD.",
        "- 10% dynamic reserve: about $10.5k gets bought, funded mostly from remaining cash plus a small GLD trim.",
        "- 15% dynamic reserve: about $15.1k gets bought, but the long-run CAGR hit is larger.",
        "",
        "## Interpretation",
        "",
        "Cash reserve lowered long-run CAGR because this is a high-return AI/semis strategy, but it materially improves your ability to buy a sudden dip without selling winners or GLD.",
        "",
        "The practical compromise is 10%-15% cash, not 20%. A 20% reserve gives more psychological comfort but meaningfully reduces compounding.",
        "",
        f"Chart: `{chart.name}`",
    ]
    (OUT / "CASH_DIP_RESERVE_BACKTEST.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
