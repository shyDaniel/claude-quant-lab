from __future__ import annotations

import json
from dataclasses import dataclass
from textwrap import shorten
from typing import Any

from openai import OpenAI

from qlab.briefing_service.config import Settings
from qlab.briefing_service.holdings import load_portfolio, load_portfolio_from_text
from qlab.briefing_service.market_data import build_market_context
from qlab.briefing_service.news import news_context


SYSTEM_PROMPT = """You are the user's calm market steward.
Style: concise, steady, a little Alfred-like. Address him as "Master Wayne" once.
Do not create new trades. Only describe what the documented strategy says.
Focus on global market context, the user's holdings, trend, risks, and reassurance.
If the strategy notes say no scheduled trade, say HOLD. If a rule trigger is unclear, say check manually.
Avoid panic language. No fiduciary claims. Keep the SMS under 1,100 characters."""


@dataclass(frozen=True)
class BriefingResult:
    body: str
    context: dict[str, Any]


def _fallback_briefing(context: dict[str, Any]) -> str:
    holdings = context["market"].get("holdings", [])
    leaders = sorted(
        [row for row in holdings if row.get("one_day") is not None],
        key=lambda row: abs(float(row["one_day"])),
        reverse=True,
    )[:3]
    moves = ", ".join(f"{row['ticker']} {row['one_day']:+.1%}" for row in leaders) or "no live moves"
    value = context["market"].get("account_value", 0.0)
    return shorten(
        "Master Wayne: dry-run briefing. Account value "
        f"${value:,.0f}; biggest visible moves: {moves}. Strategy state: "
        "taxable v3 is staged deployment, no night trades, no scheduled sells, "
        "month-end catastrophe gate only. Breathe; the rules are doing their job.",
        width=1100,
        placeholder="...",
    )


def _call_openai(settings: Settings, context: dict[str, Any]) -> str:
    if not settings.openai_api_key:
        return _fallback_briefing(context)
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.responses.create(
        model=settings.openai_model,
        instructions=SYSTEM_PROMPT,
        input=json.dumps(context, indent=2, sort_keys=True),
    )
    return shorten(response.output_text.strip(), width=1100, placeholder="...")


def build_briefing(settings: Settings) -> BriefingResult:
    if settings.holdings_json:
        portfolio = load_portfolio_from_text(settings.holdings_json, "HOLDINGS_JSON")
    else:
        portfolio = load_portfolio(settings.holdings_path)
    context = {
        "market": build_market_context(portfolio),
        "news": news_context(settings.news_feeds),
    }
    return BriefingResult(body=_call_openai(settings, context), context=context)
