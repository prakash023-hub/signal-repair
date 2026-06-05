# signal.repair

> **DeveloperWeek New York 2026** — Repair broken information signals with live-web AI agents.

Paste a health or news claim. Multi-agent pipeline extracts the claim, gathers **live web evidence** via **Nimble**, filters to **allowlisted trusted domains**, and returns a **cited verdict** (Supported / Mixed / Disputed).

**Built by:** Prakash Raj  
**Domain:** signal.repair (name.com Domain Roulette)  
**Sponsor tracks:** Nimble · name.com Domain Roulette

---

## What it does

- **Extract agent** — normalize user claim + build search query
- **Research agent** — Nimble live web search (demo fallback without API key)
- **Verdict agent** — trust-weighted synthesis with citations
- **MCP server** — typed tools + domain allowlist guardrail (not prompt-only)
- **Gradio UI** — paste claim → verdict + sources + markdown report

---

## Quick start

```bash
cd signal-repair
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Optional: live Nimble (required for Nimble sponsor prize)
export NIMBLE_API_KEY="your-key"

python app.py
# Open http://127.0.0.1:7861
```

CLI pipeline:

```bash
python multi_agent/signal_multi_agent.py "Drinking bleach cures COVID-19"
```

MCP server:

```bash
python mcp_server/signal_repair_mcp.py
```

---

## Architecture (reused from SIFT-Analyst)

| SIFT-Analyst | signal.repair |
|--------------|---------------|
| Triage agent | Extract claim agent |
| Analysis agent | Research agent (Nimble) |
| Report agent | Verdict agent |
| Forensic MCP tools | `search_allowlisted_sources`, `verify_claim` |
| Read-only mount guard | Domain allowlist guard |
| ML anomaly scorer | Source reliability scorer |

---

## Tech stack

Python · LangGraph · MCP (FastMCP) · Nimble API · Gradio · scikit-learn · httpx

---

## Demo claims

1. `Drinking bleach cures COVID-19` → **DISPUTED**
2. `Paracetamol is safe at label dose for fever` → **SUPPORTED**
3. `Vitamin C megadoses cure all cancers` → **MIXED / DISPUTED**

---

## Hackathon submission

- **Devpost:** DeveloperWeek New York 2026
- **Deadline:** Jun 10, 2026 @ 7:30 PM IST
- **Challenges:** Nimble + name.com Domain Roulette
