from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
CACHE = ROOT / "work" / "cache"
TRADING_DAYS = 252
START = "2004-01-01"
END = "2026-07-01"
START_CAPITAL = 300_000.0

MEGACAP_AI = [
    "AAPL",
    "MSFT",
    "NVDA",
    "GOOGL",
    "AMZN",
    "META",
    "AVGO",
    "AMD",
    "ADBE",
    "CRM",
    "ORCL",
    "QCOM",
    "TSLA",
    "NFLX",
]
CAPEX_AI = [
    "NVDA",
    "AMD",
    "AVGO",
    "MU",
    "SNDK",
    "MRVL",
    "STX",
    "ANET",
    "VST",
    "CEG",
    "GEV",
    "VRT",
]
BASE_TICKERS = sorted(set(["QQQ", "SPY", "BIL", "IEF"] + MEGACAP_AI + CAPEX_AI))


@dataclass(frozen=True)
class MetricRow:
    strategy: str
    window: str
    start: str
    end: str
    cagr: float
    sharpe: float
    max_drawdown: float
    worst_12m: float
    volatility: float
    turnover: float
    pretax_end: float
    deferred_ltcg_end: float
    annual_st_end: float
    tax_note: str


def download_prices() -> pd.DataFrame:
    CACHE.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE / "audit_adjclose.csv"
    if cache_path.exists():
        return pd.read_csv(cache_path, parse_dates=["Date"], index_col="Date")
    raw = yf.download(BASE_TICKERS, start=START, end=END, auto_adjust=True, progress=False)
    close = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw
    close = close.dropna(how="all").sort_index()
    close.index.name = "Date"
    close.to_csv(cache_path)
    return close


def month_end_mask(index: pd.DatetimeIndex) -> pd.Series:
    return index.to_series().groupby(index.to_period("M")).transform("max") == index


def deferred_ltcg_end(returns: pd.Series, rate: float = 0.238) -> float:
    end_value = START_CAPITAL * (1.0 + returns.dropna()).cumprod().iloc[-1]
    gain = max(end_value - START_CAPITAL, 0.0)
    return end_value - gain * rate


def annual_taxed_end(returns: pd.Series, rate: float = 0.408) -> float:
    equity = (1.0 + returns.dropna()).cumprod()
    year_end = equity.resample("YE").last()
    factor = 1.0
    previous = 1.0
    for value in year_end.values:
        gain = value / previous - 1.0
        taxed_gain = gain * (1.0 - rate) if gain > 0.0 else gain
        factor *= 1.0 + taxed_gain
        previous = value
    return START_CAPITAL * factor


def metrics(strategy: str, window: str, returns: pd.Series, turnover: float, note: str) -> MetricRow:
    d = returns.dropna()
    equity = (1.0 + d).cumprod()
    years = len(d) / TRADING_DAYS
    cagr = equity.iloc[-1] ** (1.0 / years) - 1.0
    vol = d.std() * np.sqrt(TRADING_DAYS)
    sharpe = d.mean() / d.std() * np.sqrt(TRADING_DAYS) if d.std() > 0 else np.nan
    max_dd = (equity / equity.cummax() - 1.0).min()
    worst_12m = equity.pct_change(TRADING_DAYS).min()
    return MetricRow(
        strategy=strategy,
        window=window,
        start=str(d.index[0].date()),
        end=str(d.index[-1].date()),
        cagr=cagr,
        sharpe=sharpe,
        max_drawdown=max_dd,
        worst_12m=worst_12m,
        volatility=vol,
        turnover=turnover,
        pretax_end=START_CAPITAL * equity.iloc[-1],
        deferred_ltcg_end=deferred_ltcg_end(d),
        annual_st_end=annual_taxed_end(d),
        tax_note=note,
    )


def simulate_weights(
    prices: pd.DataFrame,
    weights: pd.DataFrame,
    cost_bps: float,
) -> tuple[pd.Series, float]:
    aligned = weights.reindex(prices.index).fillna(0.0)
    returns = prices.pct_change().fillna(0.0)
    applied = aligned.shift(1).fillna(0.0)
    gross = (applied * returns).sum(axis=1)
    turnover = aligned.diff().abs().sum(axis=1).fillna(0.0)
    net = gross - turnover * cost_bps / 10_000.0
    annual_turnover = turnover.sum() / (len(prices) / TRADING_DAYS)
    return net, annual_turnover


def qqq_buyhold(px: pd.DataFrame) -> tuple[pd.Series, float]:
    return px["QQQ"].pct_change().fillna(0.0), 0.0


def qqq_momentum(px: pd.DataFrame, lookback: int, off_asset: str, cost_bps: float) -> tuple[pd.Series, float]:
    qqq = px["QQQ"]
    signal = qqq / qqq.shift(lookback) - 1.0 > 0.0
    mask = month_end_mask(px.index)
    target = pd.DataFrame(0.0, index=px.index, columns=["QQQ", off_asset])
    monthly_q = pd.Series(np.nan, index=px.index)
    monthly_q.loc[mask] = signal.loc[mask].astype(float)
    q_weight = monthly_q.ffill().fillna(0.0)
    target["QQQ"] = q_weight
    target[off_asset] = 1.0 - q_weight
    return simulate_weights(px[["QQQ", off_asset]], target, cost_bps)


def ai_momentum_top(px: pd.DataFrame, names: list[str], top_n: int, cost_bps: float) -> tuple[pd.Series, float]:
    valid = [name for name in names if name in px.columns]
    sub = px[valid].dropna(how="all")
    momentum = (sub / sub.shift(126) - 1.0).shift(1)
    mask = month_end_mask(sub.index)
    weights = pd.DataFrame(np.nan, index=sub.index, columns=valid)
    for date in sub.index[mask]:
        row = pd.Series(0.0, index=valid)
        candidates = momentum.loc[date].dropna()
        candidates = candidates[candidates > 0.0]
        selected = candidates.sort_values(ascending=False).head(top_n).index
        if len(selected) > 0:
            row.loc[selected] = 1.0 / len(selected)
        weights.loc[date] = row
    weights = weights.ffill().fillna(0.0)
    return simulate_weights(sub, weights, cost_bps)


def capex_trend_daily(px: pd.DataFrame, cost_bps: float, basket_gate: bool) -> tuple[pd.Series, float]:
    names = [name for name in CAPEX_AI if name in px.columns]
    sub = px[names].dropna(how="all")
    above = sub > sub.rolling(100).mean()
    available = sub.notna() & sub.rolling(100).count().ge(100)
    on = above & available
    if basket_gate:
        basket_nav = (1.0 + sub.pct_change().mean(axis=1).fillna(0.0)).cumprod()
        gate = basket_nav > basket_nav.rolling(100).mean()
        on = on.mul(gate, axis=0)
    counts = on.sum(axis=1).replace(0, np.nan)
    weights = on.div(counts, axis=0).fillna(0.0)
    return simulate_weights(sub, weights, cost_bps)


def blend_returns(
    left: pd.Series,
    right: pd.Series,
    right_weight: float,
) -> pd.Series:
    idx = left.index.intersection(right.index)
    return (1.0 - right_weight) * left.reindex(idx) + right_weight * right.reindex(idx)


def rows_for_window(
    name: str,
    start: str,
    strategies: dict[str, tuple[pd.Series, float, str]],
) -> list[MetricRow]:
    rows = []
    for strategy, (returns, turnover, note) in strategies.items():
        window_returns = returns.loc[start:END]
        if len(window_returns.dropna()) >= TRADING_DAYS:
            rows.append(metrics(strategy, name, window_returns, turnover, note))
    return rows


def make_strategy_set(px: pd.DataFrame) -> dict[str, tuple[pd.Series, float, str]]:
    qqq, qqq_turn = qqq_buyhold(px)
    core_bil, core_bil_turn = qqq_momentum(px, 252, "BIL", 5.0)
    core_ief, core_ief_turn = qqq_momentum(px, 252, "IEF", 5.0)
    core_63, core_63_turn = qqq_momentum(px, 63, "BIL", 5.0)
    megacap, megacap_turn = ai_momentum_top(px, MEGACAP_AI, 5, 10.0)
    capex, capex_turn = capex_trend_daily(px, 10.0, basket_gate=False)
    capex_gated, capex_gated_turn = capex_trend_daily(px, 10.0, basket_gate=True)
    blend_20_core = blend_returns(core_bil, capex_gated, 0.20)
    blend_20_qqq = blend_returns(qqq, capex_gated, 0.20)
    blend_45_qqq = blend_returns(qqq, capex_gated, 0.45)
    return {
        "QQQ buy-hold": (qqq, qqq_turn, "deferred LTCG if held"),
        "QQQ 12m mom -> BIL": (core_bil, core_bil_turn, "taxable sales on switches"),
        "QQQ 12m mom -> IEF": (core_ief, core_ief_turn, "taxable sales on switches"),
        "QQQ 3m mom -> BIL": (core_63, core_63_turn, "parameter sensitivity"),
        "Megacap AI top5 momentum": (megacap, megacap_turn, "survivorship + ST gains"),
        "AI capex 100d trend": (capex, capex_turn, "severe survivorship + ST gains"),
        "AI capex 100d + basket gate": (capex_gated, capex_gated_turn, "severe survivorship + ST gains"),
        "80% core/BIL + 20% capex gate": (
            blend_20_core,
            0.8 * core_bil_turn + 0.2 * capex_gated_turn,
            "mixed taxes; AI sleeve ST gains",
        ),
        "80% QQQ + 20% capex gate": (
            blend_20_qqq,
            0.2 * capex_gated_turn,
            "QQQ deferred; AI sleeve ST gains",
        ),
        "55% QQQ + 45% capex gate": (
            blend_45_qqq,
            0.45 * capex_gated_turn,
            "aggressive AI allocation; ST gains",
        ),
    }


def as_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def write_tables(rows: list[MetricRow]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([row.__dict__ for row in rows])
    df.to_csv(OUT / "audit_strategy_metrics.csv", index=False)
    display = df.copy()
    for col in ["cagr", "max_drawdown", "worst_12m", "volatility"]:
        display[col] = display[col].map(as_percent)
    display["sharpe"] = display["sharpe"].map(lambda x: f"{x:.2f}")
    display["turnover"] = display["turnover"].map(lambda x: f"{x:.1f}x")
    for col in ["pretax_end", "deferred_ltcg_end", "annual_st_end"]:
        display[col] = display[col].map(lambda x: f"${x:,.0f}")
    display.to_markdown(OUT / "audit_strategy_metrics.md", index=False)


def current_signal_summary(px: pd.DataFrame, strategies: dict[str, tuple[pd.Series, float, str]]) -> str:
    last = px.dropna(how="all").index.max()
    qqq = px["QQQ"].dropna()
    qqq_last = qqq.index.max()
    qqq_on = qqq.loc[qqq_last] / qqq.shift(252).loc[qqq_last] - 1.0 > 0.0
    capex_names = [name for name in CAPEX_AI if name in px.columns]
    capex = px[capex_names].loc[:last]
    ma = capex.rolling(100).mean()
    status = []
    for name in capex_names:
        if pd.isna(capex[name].iloc[-1]) or pd.isna(ma[name].iloc[-1]):
            continue
        distance = capex[name].iloc[-1] / ma[name].iloc[-1] - 1.0
        status.append((name, distance))
    active = [f"{name}({distance:+.1%})" for name, distance in status if distance > 0.0]
    near = [f"{name}({distance:+.1%})" for name, distance in status if abs(distance) <= 0.03]
    capex_gate_returns = strategies["AI capex 100d + basket gate"][0]
    capex_recent = (1.0 + capex_gate_returns.loc["2026":]).cumprod().iloc[-1] - 1.0
    return "\n".join(
        [
            f"Data through: {last.date()} (audit end parameter excludes 2026-07-01 intraday/partial data)",
            f"QQQ 12-month momentum signal as of {qqq_last.date()}: {'ON' if qqq_on else 'OFF'}",
            f"AI-capex names above 100d MA: {', '.join(active) if active else 'none'}",
            f"AI-capex names within 3% of 100d MA: {', '.join(near) if near else 'none'}",
            f"AI-capex gated sleeve 2026 YTD pre-tax return in this model: {capex_recent:+.1%}",
        ]
    )


def stress_lines() -> list[str]:
    shocks = [-0.3, -0.5, -0.7]
    weights = [0.2, 0.45, 1.0]
    lines = []
    for weight in weights:
        losses = [f"{shock:+.0%} sleeve -> {weight * shock:+.1%} account" for shock in shocks]
        lines.append(f"- AI sleeve weight {weight:.0%}: " + "; ".join(losses))
    return lines


def write_report(rows: list[MetricRow], signal_summary: str) -> None:
    df = pd.DataFrame([row.__dict__ for row in rows])
    best = df.sort_values(["window", "sharpe"], ascending=[True, False]).groupby("window").head(3)
    report = [
        "# Independent Audit Report",
        "",
        "## Data And Runtime",
        f"- Price source: yfinance adjusted close, start `{START}`, end-exclusive `{END}`.",
        "- Backtests avoid the current trading day because July 1, 2026 may be partial/intraday.",
        "- Package versions captured by `uv pip install`: pandas 3.0.3, numpy 2.5.0, yfinance 1.5.1.",
        "- Repo under review was left unmodified; audit code lives in `work/`.",
        "",
        "## Current Mechanical Signals",
        signal_summary,
        "",
        "## Top Sharpe Rows By Window",
        best.to_markdown(index=False),
        "",
        "## AI Crash Sleeve Stress",
        *stress_lines(),
        "",
        "## Audit Notes",
        "- exp01-exp18 reran successfully and broadly reproduce the repo's reported numbers.",
        "- exp19-exp21 claims are not reproducible from committed source; only documentation exists.",
        "- The AI-capex strategy is a current-winners basket, so its 5-10 year result is not a fair",
        "  point-in-time universe backtest.",
        "- A 45% AI sleeve can dominate recent backtests but creates a large single-theme crash loss.",
        "- Taxable-account deployment should discount high-turnover sleeves heavily; many gains are",
        "  short-term or realized on switches.",
        "",
        "Full metric table: `audit_strategy_metrics.md` and `audit_strategy_metrics.csv`.",
    ]
    (OUT / "INDEPENDENT_AUDIT.md").write_text("\n".join(report) + "\n")


def main() -> None:
    px = download_prices()
    strategies = make_strategy_set(px)
    windows = {
        "5y": "2021-07-01",
        "10y": "2016-07-01",
        "13y_ai": "2013-01-01",
        "full_available": "2007-01-01",
    }
    rows: list[MetricRow] = []
    for window, start in windows.items():
        rows.extend(rows_for_window(window, start, strategies))
    write_tables(rows)
    write_report(rows, current_signal_summary(px, strategies))


if __name__ == "__main__":
    main()
