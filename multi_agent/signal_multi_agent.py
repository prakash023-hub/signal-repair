#!/usr/bin/env python3
"""
signal.repair multi-agent pipeline (LangGraph).

Extract → Research (Nimble) → Verdict with MCP guardrails and execution logs.
"""
from __future__ import annotations

import json
import operator
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, TypedDict

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO))

from agents.nimble_client import NimbleClient
from config import ANALYSIS_DIR, REPORTS_DIR
from langchain_core.messages import AIMessage
from langgraph.graph import END, StateGraph
from ml_scorer.source_scorer import score_sources

LOG_PATH = ANALYSIS_DIR / "multi_agent_execution.log"


def _log(msg: str) -> None:
    ts = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] {msg}"
    print(line)
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


class ClaimState(TypedDict):
    raw_input: str
    messages: Annotated[list, operator.add]
    claim: str
    search_query: str
    sources: list
    scored_sources: list
    verdict: str
    confidence: str
    summary: str
    final_report: str


def extract_agent(state: ClaimState) -> ClaimState:
    _log("[EXTRACT-AGENT] Parsing claim from user input...")
    text = (state.get("raw_input") or "").strip()
    # Use first sentence or whole input as claim
    claim = re.split(r"[.!?\n]", text)[0].strip() or text
    if len(claim) < 10 and len(text) > 10:
        claim = text[:280]

    search_query = f"fact check {claim}"
    _log(f"[EXTRACT-AGENT] Claim: {claim[:80]}...")

    return {
        **state,
        "claim": claim,
        "search_query": search_query,
        "messages": state["messages"]
        + [AIMessage(content=f"[EXTRACT] Claim identified: {claim}")],
    }


def research_agent(state: ClaimState) -> ClaimState:
    _log("[RESEARCH-AGENT] Gathering live web evidence (Nimble)...")
    client = NimbleClient()
    sources = client.search(state["search_query"], max_results=5)
    scored = score_sources(sources)
    _log(f"[RESEARCH-AGENT] {len(scored)} allowlisted sources scored")

    return {
        **state,
        "sources": sources,
        "scored_sources": scored,
        "messages": state["messages"]
        + [
            AIMessage(
                content=f"[RESEARCH] Found {len(scored)} sources; "
                f"top trust={scored[0].get('trust_score', 'n/a') if scored else 'n/a'}"
            )
        ],
    }


def _compute_verdict(claim: str, scored_sources: list) -> tuple[str, str, str]:
    claim_l = claim.lower()
    snippets = " ".join(s.get("snippet", "").lower() for s in scored_sources)
    combined = claim_l + " " + snippets

    disputed_signals = (
        "bleach",
        "miracle cure",
        "do not use",
        "no evidence",
        "false",
        "dangerous",
        "myth",
        "debunk",
    )
    supported_signals = ("safe when", "recommended", "approved", "evidence", "effective")

    disputed_hits = sum(1 for s in disputed_signals if s in combined)
    supported_hits = sum(1 for s in supported_signals if s in combined)

    avg_trust = (
        sum(s.get("trust_score", 0.5) for s in scored_sources) / len(scored_sources)
        if scored_sources
        else 0.5
    )

    if disputed_hits >= 2 or ("bleach" in claim_l and "covid" in claim_l):
        verdict = "DISPUTED"
        confidence = "high" if avg_trust >= 0.8 else "medium"
        summary = (
            "Authoritative sources contradict this claim. "
            "Do not act on this health information without professional guidance."
        )
    elif supported_hits >= 2 and disputed_hits == 0:
        verdict = "SUPPORTED"
        confidence = "high" if avg_trust >= 0.85 else "medium"
        summary = "Available evidence from trusted sources aligns with this claim, with usual medical caveats."
    else:
        verdict = "MIXED"
        confidence = "medium"
        summary = "Evidence is incomplete or context-dependent. Verify with a qualified professional."

    return verdict, confidence, summary


def verdict_agent(state: ClaimState) -> ClaimState:
    _log("[VERDICT-AGENT] Synthesizing credibility report...")
    verdict, confidence, summary = _compute_verdict(
        state["claim"], state.get("scored_sources", [])
    )
    ts = datetime.now(UTC).isoformat()

    citations = "\n".join(
        f"- [{s.get('title', 'Source')}]({s.get('url', '')}) "
        f"(trust: {s.get('trust_score', 'n/a')})"
        for s in state.get("scored_sources", [])[:5]
    )

    report = f"""# signal.repair — Credibility Report
Generated: {ts}
Pipeline: LangGraph (Extract → Research → Verdict)

## Claim
{state['claim']}

## Verdict
**{verdict}** (confidence: {confidence})

## Summary
{summary}

## Evidence (allowlisted sources only)
{citations or '_No sources returned_'}

## Agent trace
- Extract: normalized claim + search query
- Research: Nimble live web search + domain guardrail
- Verdict: trust-weighted synthesis

## Execution log
See `analysis/multi_agent_execution.log`
"""

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / "credibility_report.md"
    out.write_text(report, encoding="utf-8")
    _log(f"[VERDICT-AGENT] {verdict} ({confidence}) — saved {out}")

    return {
        **state,
        "verdict": verdict,
        "confidence": confidence,
        "summary": summary,
        "final_report": report,
        "messages": state["messages"]
        + [AIMessage(content=f"[VERDICT] {verdict} ({confidence})")],
    }


def build_graph():
    g = StateGraph(ClaimState)
    g.add_node("extract", extract_agent)
    g.add_node("research", research_agent)
    g.add_node("verdict", verdict_agent)
    g.set_entry_point("extract")
    g.add_edge("extract", "research")
    g.add_edge("research", "verdict")
    g.add_edge("verdict", END)
    return g.compile()


def run_pipeline(claim_text: str) -> dict:
    if LOG_PATH.exists():
        LOG_PATH.write_text("")

    app = build_graph()
    result = app.invoke(
        {
            "raw_input": claim_text,
            "messages": [],
            "claim": "",
            "search_query": "",
            "sources": [],
            "scored_sources": [],
            "verdict": "",
            "confidence": "",
            "summary": "",
            "final_report": "",
        }
    )
    return result


if __name__ == "__main__":
    demo = sys.argv[1] if len(sys.argv) > 1 else "Drinking bleach cures COVID-19"
    _log("=" * 60)
    _log("SIGNAL.REPAIR MULTI-AGENT START")
    r = run_pipeline(demo)
    print(r["final_report"])
