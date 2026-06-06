#!/usr/bin/env python3
"""Quick test: verify NIMBLE_API_KEY works with live search."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.nimble_client import NimbleClient
from config import NIMBLE_API_KEY


def main():
    if not NIMBLE_API_KEY:
        print("❌ NIMBLE_API_KEY not set.")
        print("   cp .env.example .env")
        print("   # edit .env and add your key")
        print("   OR: export NIMBLE_API_KEY='your-key'")
        sys.exit(1)

    client = NimbleClient()
    print(f"✅ API key loaded ({NIMBLE_API_KEY[:8]}...)")
    print(f"   Live mode: {client.is_live}")
    print("🔍 Searching: fact check drinking bleach covid...\n")

    results = client.search("fact check drinking bleach covid", max_results=3)
    for i, r in enumerate(results, 1):
        print(f"{i}. [{r.get('source')}] {r.get('title')}")
        print(f"   {r.get('url')}")
        print(f"   {r.get('snippet', '')[:120]}...")
        if r.get("nimble_answer"):
            print(f"   Nimble answer: {r['nimble_answer'][:120]}...")
        print()

    if results and results[0].get("source") == "nimble":
        print("✅ Live Nimble search working — ready for demo video!")
    elif results and results[0].get("source") == "error":
        print("❌ Nimble returned an error — check key or API params.")
        sys.exit(1)
    else:
        print("⚠️  Fell back to demo sources — check API response.")


if __name__ == "__main__":
    main()
