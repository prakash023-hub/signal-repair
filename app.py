"""
signal.repair — Gradio web app
Repair broken information signals with live-web agent verification.

Run: python app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gradio as gr
from agents.nimble_client import NimbleClient
from multi_agent.signal_multi_agent import run_pipeline

_nimble = NimbleClient()
NIMBLE_BADGE = (
    "🟢 **Live web:** Nimble Search API active"
    if _nimble.is_live
    else "🟡 **Demo mode:** set `NIMBLE_API_KEY` in `.env` for live Nimble"
)

EXAMPLE_CLAIMS = [
    "Drinking bleach cures COVID-19",
    "Paracetamol is safe at label dose for fever",
    "Vitamin C megadoses cure all cancers",
]


def analyze_claim(claim_text: str):
    if not claim_text or not claim_text.strip():
        return "⚠️ Enter a claim to verify.", "", ""

    result = run_pipeline(claim_text.strip())

    details = (
        f"🔍 Claim: {result['claim']}\n\n"
        f"📊 Verdict: {result['verdict']}\n"
        f"📈 Confidence: {result['confidence'].upper()}\n\n"
        f"📝 Summary:\n{result['summary']}\n\n"
        f"🌐 Sources ({len(result.get('scored_sources', []))}):\n"
    )
    for s in result.get("scored_sources", [])[:5]:
        details += (
            f"\n• {s.get('title', 'Source')}\n"
            f"  {s.get('url', '')}\n"
            f"  trust={s.get('trust_score', 'n/a')} ({s.get('tier', '')})\n"
            f"  {s.get('snippet', '')[:120]}...\n"
        )

    report = result.get("final_report", "")
    verdict_badge = f"**{result['verdict']}** — {result['confidence']} confidence"

    return verdict_badge, details, report


def build_ui():
    with gr.Blocks(title="signal.repair — Repair Broken Information") as demo:
        gr.HTML(f"""
        <div style="text-align:center; padding:16px 0;">
            <h1 style="margin:0; color:#0f766e;">signal.repair</h1>
            <p style="color:#444;">Paste a health or news claim → agents gather live evidence → cited verdict</p>
            <p style="font-size:0.9rem; color:#666;">DeveloperWeek NY 2026 · Nimble + LangGraph + MCP guardrails</p>
            <p style="font-size:0.85rem; color:#0f766e;">{NIMBLE_BADGE}</p>
        </div>
        """)

        with gr.Row():
            claim_in = gr.Textbox(
                label="Claim to verify",
                placeholder="e.g. Drinking bleach cures COVID-19",
                lines=3,
            )

        with gr.Row():
            gr.Examples(examples=[[c] for c in EXAMPLE_CLAIMS], inputs=claim_in)

        verify_btn = gr.Button("🔧 Repair Signal — Verify Claim", variant="primary", size="lg")

        verdict_out = gr.Markdown(label="Verdict")
        details_out = gr.Textbox(label="Evidence & sources", lines=14)
        report_out = gr.Markdown(label="Full report")

        verify_btn.click(
            fn=analyze_claim,
            inputs=[claim_in],
            outputs=[verdict_out, details_out, report_out],
        )

        gr.HTML("""
        <div style="background:#ecfdf5; border-radius:8px; padding:12px; margin-top:12px; font-size:0.9rem;">
            <b>Pipeline:</b> Extract claim → Nimble live web search → allowlisted sources only → verdict report<br>
            <b>Built by:</b> Prakash Raj · <b>Domain:</b> signal.repair
        </div>
        """)

    return demo


if __name__ == "__main__":
    app = build_ui()
    app.launch(server_name="0.0.0.0", server_port=7861, share=True, show_error=True)
