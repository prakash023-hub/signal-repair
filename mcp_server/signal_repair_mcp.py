#!/usr/bin/env python3
"""
signal.repair MCP server — typed tools with domain allowlist guardrails.
"""
from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from agents.nimble_client import NimbleClient, _domain_allowed
from config import ALLOWLISTED_DOMAINS
from mcp.server.fastmcp import FastMCP
from ml_scorer.source_scorer import score_source, score_sources

mcp = FastMCP("signal-repair")


def _ts() -> str:
    return datetime.now(UTC).isoformat()


@mcp.tool()
def search_allowlisted_sources(query: str, max_results: int = 5) -> str:
    """Search the live web via Nimble; results filtered to allowlisted domains only."""
    client = NimbleClient()
    results = client.search(query, max_results=max_results)
    return json.dumps({"timestamp": _ts(), "query": query, "results": results}, indent=2)


@mcp.tool()
def score_source_reliability(url: str, snippet: str = "") -> str:
    """Score a source URL by domain trust tier and snippet signals."""
    if url and not _domain_allowed(url):
        return json.dumps(
            {
                "timestamp": _ts(),
                "status": "blocked",
                "reason": "domain not on allowlist",
                "allowlist": list(ALLOWLISTED_DOMAINS),
            },
            indent=2,
        )
    return json.dumps({"timestamp": _ts(), **score_source(url, snippet)}, indent=2)


@mcp.tool()
def verify_claim(claim: str) -> str:
    """Run full signal.repair pipeline: extract → research → verdict."""
    from multi_agent.signal_multi_agent import run_pipeline

    result = run_pipeline(claim)
    return json.dumps(
        {
            "timestamp": _ts(),
            "claim": result.get("claim"),
            "verdict": result.get("verdict"),
            "confidence": result.get("confidence"),
            "summary": result.get("summary"),
            "sources": result.get("scored_sources", [])[:5],
        },
        indent=2,
    )


if __name__ == "__main__":
    mcp.run()
