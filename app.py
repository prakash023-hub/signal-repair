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

# Full-width layout — Gradio defaults to a narrow centered column.
FULLSCREEN_CSS = """
html, body { height: 100%; margin: 0; }
.gradio-container {
    max-width: 100% !important;
    width: 100% !important;
    min-height: 100vh !important;
    padding: 12px 32px 32px !important;
    box-sizing: border-box !important;
}
.contain, .main, .wrap, .app, .block, .form {
    max-width: 100% !important;
    width: 100% !important;
}
.gradio-row { width: 100% !important; flex-wrap: wrap !important; }
.gradio-column { width: 100% !important; min-width: 0 !important; }
.gr-textbox, .gr-textbox > div, .gr-textbox textarea, .gr-textbox input {
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
}
.gr-button-lg { min-height: 48px !important; }
footer { display: none !important; }
.signal-repair-footer, .signal-repair-footer * {
    color: #134e4a !important;
}
"""


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
    with gr.Blocks(
        title="signal.repair — Repair Broken Information",
        css=FULLSCREEN_CSS,
        fill_width=True,
        fill_height=True,
    ) as demo:
        gr.HTML(f"""
        <div style="text-align:center; padding:16px 0; width:100%;">
            <h1 style="margin:0; color:#0f766e;">signal.repair</h1>
            <p style="color:#444;">Paste a health or news claim → agents gather live evidence → cited verdict</p>
            <p style="font-size:0.9rem; color:#666;">DeveloperWeek NY 2026 · Nimble + LangGraph + MCP guardrails</p>
            <p style="font-size:0.85rem; color:#0f766e;">{NIMBLE_BADGE}</p>
        </div>
        """)

        claim_in = gr.Textbox(
            label="Claim to verify",
            placeholder="e.g. Drinking bleach cures COVID-19",
            lines=4,
            max_lines=6,
        )

        verify_btn = gr.Button(
            "🔧 Repair Signal — Verify Claim",
            variant="primary",
            size="lg",
        )

        gr.Examples(examples=[[c] for c in EXAMPLE_CLAIMS], inputs=claim_in)

        verdict_out = gr.Markdown(label="Verdict")
        details_out = gr.Textbox(
            label="Evidence & sources",
            lines=16,
            max_lines=30,
        )
        report_out = gr.Markdown(label="Full report")

        verify_btn.click(
            fn=analyze_claim,
            inputs=[claim_in],
            outputs=[verdict_out, details_out, report_out],
        )

        gr.HTML("""
        <div class="signal-repair-footer" style="
            background:#ecfdf5;
            border-radius:8px;
            border-left:4px solid #0f766e;
            padding:14px 16px;
            margin-top:16px;
            font-size:0.95rem;
            width:100%;
            box-sizing:border-box;
            color:#134e4a !important;
        ">
            <p style="margin:0 0 6px 0; color:#134e4a !important;">
                <b style="color:#0f766e !important;">Pipeline:</b>
                <span style="color:#134e4a !important;">
                    Extract claim → Nimble live web search → allowlisted sources only → verdict report
                </span>
            </p>
            <p style="margin:0; color:#134e4a !important;">
                <b style="color:#0f766e !important;">Built by:</b>
                <span style="color:#134e4a !important;"> Prakash Raj · </span>
                <b style="color:#0f766e !important;">Domain:</b>
                <span style="color:#134e4a !important;"> signal.repair</span>
            </p>
        </div>
        """)

    return demo


if __name__ == "__main__":
    app = build_ui()
    app.launch(server_name="0.0.0.0", server_port=7861, share=True, show_error=True)
