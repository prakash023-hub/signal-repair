"""Nimble API client for live web search and extraction."""
from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlparse

import httpx

from config import ALLOWLISTED_DOMAINS, DEMO_MODE, NIMBLE_API_KEY, NIMBLE_BASE_URL


def _domain_allowed(url: str) -> bool:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    return any(host == d or host.endswith("." + d) for d in ALLOWLISTED_DOMAINS)


def _demo_sources(query: str) -> list[dict[str, Any]]:
    """Bundled sources for judge demos when Nimble key is not set."""
    q = query.lower()
    if "bleach" in q or "covid" in q:
        return [
            {
                "title": "WHO — COVID-19 myth busters",
                "url": "https://www.who.int/emergencies/diseases/novel-coronavirus-2019/advice-for-public/myth-busters",
                "snippet": "Do not use bleach or disinfectant on your body. These substances are dangerous.",
                "source": "demo",
            },
            {
                "title": "CDC — COVID-19 Treatment",
                "url": "https://www.cdc.gov/coronavirus/2019-ncov/your-health/treatments.html",
                "snippet": "There is no evidence that drinking bleach treats COVID-19.",
                "source": "demo",
            },
        ]
    if "medicine" in q or "paracetamol" in q or "acetaminophen" in q:
        return [
            {
                "title": "FDA — Acetaminophen safety",
                "url": "https://www.fda.gov/drugs",
                "snippet": "When used as directed, acetaminophen is safe and effective for pain and fever.",
                "source": "demo",
            },
            {
                "title": "Mayo Clinic — Pain relievers",
                "url": "https://www.mayoclinic.org",
                "snippet": "Follow label dosing. Overdose can cause liver damage.",
                "source": "demo",
            },
        ]
    return [
        {
            "title": "Reuters — Fact check",
            "url": "https://www.reuters.com/fact-check/",
            "snippet": "Independent fact-checkers evaluate viral claims against primary sources.",
            "source": "demo",
        },
        {
            "title": "WHO — Health topics",
            "url": "https://www.who.int/health-topics",
            "snippet": "Consult authoritative health agencies for medical claims.",
            "source": "demo",
        },
    ]


class NimbleClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or NIMBLE_API_KEY
        self.use_demo = not self.api_key and DEMO_MODE in ("auto", "1", "true", "yes")

    def search(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        if self.use_demo:
            return _demo_sources(query)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "query": query,
            "max_results": max_results,
            "search_depth": "lite",
            "include_answer": True,
        }
        try:
            with httpx.Client(timeout=60.0) as client:
                resp = client.post(f"{NIMBLE_BASE_URL}/search", headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:
            return [{"title": "Nimble error", "url": "", "snippet": str(exc), "source": "error"}]

        results: list[dict[str, Any]] = []
        for item in data.get("results", data.get("data", []))[:max_results]:
            if isinstance(item, dict):
                url = item.get("url", "")
                if url and not _domain_allowed(url):
                    continue
                results.append(
                    {
                        "title": item.get("title", "Untitled"),
                        "url": url,
                        "snippet": item.get("snippet", item.get("content", ""))[:500],
                        "source": "nimble",
                    }
                )
        return results or _demo_sources(query)
