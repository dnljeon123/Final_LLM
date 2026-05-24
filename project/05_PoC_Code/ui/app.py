"""
Gradio UI Application (Owner: Member 4)
End-to-end demo: paste text → preprocess → LLM analyze → display result.

Run: python ui/app.py
Make sure GEMINI_API_KEY is set in environment or .env file.
"""
import os
import sys
from pathlib import Path

# Add parent dir to path so relative imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

import gradio as gr
from dotenv import load_dotenv

from data.preprocessing import process
from llm_core.client import LLMClient

load_dotenv()

# Initialize LLM client once at startup
try:
    llm = LLMClient()
    LLM_READY = True
except ValueError as e:
    print(f"WARNING: {e}. UI will run in mock mode.")
    llm = None
    LLM_READY = False


VERDICT_EMOJI = {"phishing": "⚠️ PHISHING", "safe": "✅ SAFE", "suspect": "🟡 SUSPECT"}
VERDICT_COLOR = {"phishing": "#dc3545", "safe": "#28a745", "suspect": "#ffc107"}


def analyze_message(text: str, strategy: str) -> tuple:
    """Main pipeline: preprocess + analyze + format."""
    if not text or not text.strip():
        return "❌ Please enter a message", 0.0, "<p>No content to analyze</p>", ""

    # Preprocess (M1)
    preprocessed = process({"type": "text", "raw_content": text})

    # Analyze (M2)
    if LLM_READY:
        result = llm.analyze(preprocessed, strategy=strategy)
    else:
        # Mock fallback
        result = {
            "label": "suspect",
            "confidence": 0.5,
            "red_flags": ["MOCK MODE — set GEMINI_API_KEY to use real LLM"],
            "reasoning": {"note": "LLM not initialized"},
            "processing_time_ms": 0,
        }

    # Format output (M4)
    label = result["label"]
    verdict_html = f"""
    <div style='padding:15px;border-radius:8px;
                background-color:{VERDICT_COLOR[label]};color:white;
                font-size:20px;font-weight:bold;text-align:center;'>
        {VERDICT_EMOJI[label]}
    </div>
    """

    flags = result.get("red_flags", [])
    flags_html = "<h4>🚩 Red flags detected:</h4>"
    if flags:
        flags_html += "<ul>" + "".join(f"<li>{f}</li>" for f in flags) + "</ul>"
    else:
        flags_html += "<p><i>None detected.</i></p>"

    flags_html += f"<p><small>⏱ Processing time: {result.get('processing_time_ms', 0)}ms | Strategy: {result.get('strategy', strategy)}</small></p>"

    reasoning = result.get("reasoning") or {}
    reasoning_text = ""
    if reasoning:
        reasoning_text = "\n".join(f"**{k}:** {v}" for k, v in reasoning.items())

    return verdict_html, result["confidence"], flags_html, reasoning_text


EXAMPLE_PHISHING = """URGENT: Your PayPal account has been temporarily suspended due to suspicious activity.

To restore access, please verify your identity within 24 hours by clicking the link below:
https://paypa1-secure-verify.com/login

Failure to verify will result in permanent account closure.

PayPal Security Team"""

EXAMPLE_SAFE = """Hi Sarah,

Just confirming our meeting tomorrow at 2pm in conference room B. I'll bring the Q4 numbers we discussed.

Let me know if you need to reschedule.

Thanks,
Mike"""


def build_ui():
    with gr.Blocks(theme=gr.themes.Soft(), title="🛡️ Phishing Detector") as app:
        gr.Markdown(
            """
            # 🛡️ Phishing Detector — Powered by Gemini LLM
            ### Term Project — LLM in Cybersecurity
            Paste an email or SMS below and the LLM will classify it. Choose a prompting strategy to compare techniques.
            """
        )

        with gr.Row():
            with gr.Column(scale=2):
                text_input = gr.Textbox(
                    lines=10,
                    label="📨 Message content",
                    placeholder="Paste email or SMS here...",
                )
                strategy = gr.Radio(
                    choices=["zero_shot", "few_shot", "cot"],
                    value="cot",
                    label="🧠 Prompting Strategy",
                    info="Chain-of-Thought (cot) recommended for best results.",
                )
                analyze_btn = gr.Button("🔍 Analyze", variant="primary", size="lg")

                gr.Examples(
                    examples=[
                        [EXAMPLE_PHISHING, "cot"],
                        [EXAMPLE_SAFE, "cot"],
                    ],
                    inputs=[text_input, strategy],
                    label="📋 Try these examples",
                )

            with gr.Column(scale=2):
                verdict_out = gr.HTML(label="Verdict")
                confidence_out = gr.Slider(0, 1, label="🎯 Confidence", interactive=False)
                flags_out = gr.HTML(label="Analysis")
                with gr.Accordion("🧩 Reasoning steps (CoT only)", open=False):
                    reasoning_out = gr.Markdown()

        analyze_btn.click(
            analyze_message,
            inputs=[text_input, strategy],
            outputs=[verdict_out, confidence_out, flags_out, reasoning_out],
        )

        gr.Markdown(
            """
            ---
            **Note:** This is a Proof of Concept. Always verify with your IT/security team before acting on important emails.
            """
        )

    return app


if __name__ == "__main__":
    app = build_ui()
    app.launch(server_name="0.0.0.0", server_port=7860)
