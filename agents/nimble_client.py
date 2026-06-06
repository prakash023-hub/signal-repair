"""Nimble API client for live web search and extraction."""
from __future__ import annotations

import time
from typing import Any
from urllib.parse import urlparse

import httpx

from config import ALLOWLISTED_DOMAINS, DEMO_MODE, NIMBLE_API_KEY, NIMBLE_BASE_URL


def _domain_allowed(url: str) -> bool:
    if not url:
        return False
    host = urlparse(url).netloc.lower().removeprefix("www.")
    return any(host == d or host.endswith("." + d) for d in ALLOWLISTED_DOMAINS)


def _demo_sources(query: str) -> list[dict[str, Any]]:
    """Fallback when no API key (local dev only)."""
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


def _parse_search_results(data: dict, max_results: int) -> list[dict[str, Any]]:
    """Normalize Nimble search JSON into uniform source dicts."""
    items = data.get("results") or data.get("data") or []
    if not isinstance(items, list):
        return []

    parsed: list[dict[str, Any]] = []
    for item in items[: max_results * 2]:
        if not isinstance(item, dict):
            continue
        url = item.get("url") or item.get("link") or ""
        snippet = (
            item.get("snippet")
            or item.get("description")
            or item.get("content")
            or ""
        )
        parsed.append(
            {
                "title": item.get("title") or "Untitled",
                "url": url,
                "snippet": str(snippet)[:500],
                "source": "nimble",
            }
        )
        if len(parsed) >= max_results:
            break
    return parsed


def _poll_async_task(client: httpx.Client, headers: dict, task_id: str) -> dict:
    """Poll Nimble async task until complete (max ~90s)."""
    status_url = f"{NIMBLE_BASE_URL}/tasks/{task_id}"
    results_url = f"{NIMBLE_BASE_URL}/tasks/{task_id}/results"

    for _ in range(30):
        status_resp = client.get(status_url, headers=headers)
        status_resp.raise_for_status()
        status_data = status_resp.json()
        state = (status_data.get("status") or status_data.get("state") or "").lower()

        if state in ("completed", "success", "done"):
            res = client.get(results_url, headers=headers)
            res.raise_for_status()
            return res.json()
        if state in ("failed", "error"):
            raise RuntimeError(f"Nimble task failed: {status_data}")

        time.sleep(3)

    raise TimeoutError("Nimble async search timed out")


class NimbleClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or NIMBLE_API_KEY
        placeholder = "your-nimble-api-key-here"
        self.use_demo = (
            not self.api_key or self.api_key == placeholder
        ) and DEMO_MODE in ("auto", "1", "true", "yes")

    @property
    def is_live(self) -> bool:
        return bool(self.api_key) and not self.use_demo

    def search(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        if self.use_demo:
            return _demo_sources(query)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        # Use Nimble include_domains — architectural guardrail at API level
        # Hackathon API keys support minimal search payload only.
        # Extra params (include_domains, focus, include_answer) return 403 on trial tier.
        # Trust filtering happens in source_scorer after live results return.
        payload = {
            "query": query,
            "max_results": max_results,
        }

        try:
            with httpx.Client(timeout=90.0) as client:
                resp = client.post(f"{NIMBLE_BASE_URL}/search", headers=headers, json=payload)

                # Some accounts return 202 + task_id for async search
                if resp.status_code == 202:
                    task_id = resp.json().get("task_id")
                    if task_id:
                        data = _poll_async_task(client, headers, task_id)
                    else:
                        data = resp.json()
                else:
                    resp.raise_for_status()
                    data = resp.json()

                results = _parse_search_results(data, max_results)

                # Attach Nimble LLM answer if present
                answer = data.get("answer")
                if answer and results:
                    results[0]["nimble_answer"] = str(answer)[:400]

                return results or _demo_sources(query)

        except Exception as exc:
            return [
                {
                    "title": "Nimble API error",
                    "url": "",
                    "snippet": str(exc),
                    "source": "error",
                }
            ]
