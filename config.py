"""signal.repair — paths, allowlists, and environment configuration."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(os.environ.get("SIGNAL_REPAIR_ROOT", Path(__file__).resolve().parent)).expanduser()
ANALYSIS_DIR = Path(os.environ.get("SIGNAL_REPAIR_ANALYSIS", ROOT / "analysis")).expanduser()
REPORTS_DIR = Path(os.environ.get("SIGNAL_REPAIR_REPORTS", ROOT / "reports")).expanduser()

NIMBLE_API_KEY = os.environ.get("NIMBLE_API_KEY", "")
NIMBLE_BASE_URL = os.environ.get("NIMBLE_BASE_URL", "https://sdk.nimbleway.com/v1")

# Architectural guardrail: only these domains may be fetched/scored as evidence
ALLOWLISTED_DOMAINS: tuple[str, ...] = (
    "who.int",
    "cdc.gov",
    "nih.gov",
    "ncbi.nlm.nih.gov",
    "pubmed.ncbi.nlm.nih.gov",
    "reuters.com",
    "apnews.com",
    "bbc.com",
    "nature.com",
    "sciencedirect.com",
    "healthline.com",
    "mayoclinic.org",
    "fda.gov",
)

DOMAIN_TRUST: dict[str, float] = {
    "who.int": 0.98,
    "cdc.gov": 0.97,
    "fda.gov": 0.97,
    "nih.gov": 0.96,
    "ncbi.nlm.nih.gov": 0.95,
    "pubmed.ncbi.nlm.nih.gov": 0.95,
    "reuters.com": 0.90,
    "apnews.com": 0.90,
    "bbc.com": 0.88,
    "nature.com": 0.92,
    "mayoclinic.org": 0.89,
    "healthline.com": 0.82,
}

DEMO_MODE = os.environ.get("SIGNAL_REPAIR_DEMO", "auto").lower()
# auto = use demo sources when NIMBLE_API_KEY is missing
