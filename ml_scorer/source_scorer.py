"""Score source reliability from domain trust and snippet signals."""
from __future__ import annotations

import re
from urllib.parse import urlparse

from config import DOMAIN_TRUST


def _host(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def score_source(url: str, snippet: str = "") -> dict:
    host = _host(url)
    trust = 0.5
    for domain, score in DOMAIN_TRUST.items():
        if host == domain or host.endswith("." + domain):
            trust = score
            break

    text = snippet.lower()
    caution_words = ("myth", "false", "misinformation", "no evidence", "debunk", "dangerous")
    support_words = ("evidence", "study", "recommended", "safe when", "approved")

    caution_hits = sum(1 for w in caution_words if w in text)
    support_hits = sum(1 for w in support_words if w in text)

    adjustment = 0.03 * support_hits - 0.04 * caution_hits
    final = max(0.0, min(1.0, trust + adjustment))

    return {
        "url": url,
        "domain": host,
        "trust_score": round(final, 3),
        "tier": "high" if final >= 0.85 else "medium" if final >= 0.65 else "low",
    }


def score_sources(sources: list[dict]) -> list[dict]:
    scored = []
    for src in sources:
        s = score_source(src.get("url", ""), src.get("snippet", ""))
        scored.append({**src, **s})
    return sorted(scored, key=lambda x: x.get("trust_score", 0), reverse=True)
