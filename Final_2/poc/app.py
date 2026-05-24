"""Gradio web demo for the phishing detection PoC."""
from __future__ import annotations

import json
from pathlib import Path

import gradio as gr

from pipeline import analyze_single
from config import GRADIO_PORT, GRADIO_SHARE, SAMPLES_DIR


# --- Load demo samples for quick-fill buttons ---
def _load_samples() -> list[dict]:
    samples_file = SAMPLES_DIR / "demo_samples.json"
    if samples_file.exists():
        with open(samples_file, encoding="utf-8") as f:
            return json.load(f)
    return []


SAMPLES = _load_samples()


# --- UI styling helpers ---
VERDICT_COLOR = {
    "phishing": "#D32F2F",  # red
    "suspect":  "#F57C00",  # amber
    "safe":     "#2E7D32",  # green
}

VERDICT_EMOJI = {
    "phishing": "🚨",
    "suspect":  "⚠️",
    "safe":     "✅",
}


def _format_verdict_html(result: dict) -> str:
    verdict = result["verdict"]
    confidence = result["confidence"]
    color = VERDICT_COLOR.get(verdict, "#666666")
    emoji = VERDICT_EMOJI.get(verdict, "❓")
    return f"""
    <div style='padding: 16px; border-radius: 8px;
                background: {color}15; border-left: 5px solid {color};
                font-family: sans-serif;'>
        <div style='font-size: 24px; font-weight: bold; color: {color};'>
            {emoji} {verdict.upper()}
        </div>
        <div style='margin-top: 8px; color: #333;'>
            Confidence: <b>{confidence:.0%}</b> &nbsp;|&nbsp;
            Strategy: <b>{result.get('strategy', 'n/a')}</b> &nbsp;|&nbsp;
            Latency: <b>{result.get('latency_ms', 0)} ms</b>
        </div>
    </div>
    """


def _format_red_flags_html(flags: list[str]) -> str:
    if not flags:
        return "<div style='color: #666; font-style: italic;'>No red flags detected.</div>"
    chips = "".join(
        f"<span style='display:inline-block; background:#FFEBEE; color:#C62828; "
        f"padding:4px 10px; margin:3px; border-radius:12px; font-size:13px;'>"
        f"⚑ {f}</span>"
        for f in flags
    )
    return f"<div>{chips}</div>"


def _format_extras_html(result: dict) -> str:
    urls = result.get("extracted_urls", [])
    auth = result.get("auth_status", {})
    parts = []
    if urls:
        urls_html = "<br>".join(f"&nbsp;&nbsp;• <code>{u}</code>" for u in urls[:10])
        parts.append(f"<b>Extracted URLs ({len(urls)}):</b><br>{urls_html}")
    if auth:
        auth_html = ", ".join(f"<code>{k}={v}</code>" for k, v in auth.items())
        parts.append(f"<b>Authentication:</b> {auth_html}")
    if not parts:
        return ""
    return "<div style='margin-top: 8px; color: #555; font-size: 13px;'>" + \
           "<br><br>".join(parts) + "</div>"


def run_analysis(text: str, strategy: str, file_obj) -> tuple[str, str, str, str]:
    """Main handler — called when user clicks Analyze."""
    # Prefer uploaded file over textarea if both present
    if file_obj is not None:
        try:
            source = Path(file_obj.name) if hasattr(file_obj, "name") else file_obj
            result = analyze_single(source, strategy=strategy)
        except Exception as e:
            return _error_box(f"Failed to read file: {e}"), "", "", ""
    elif text and text.strip():
        try:
            result = analyze_single(text.strip(), strategy=strategy)
        except Exception as e:
            return _error_box(f"Analysis failed: {e}"), "", "", ""
    else:
        return _error_box("Please paste a message or upload an .eml file."), "", "", ""

    verdict_html = _format_verdict_html(result)
    flags_html = _format_red_flags_html(result["red_flags"])
    reasoning = result["reasoning"]
    extras_html = _format_extras_html(result)
    return verdict_html, flags_html, reasoning, extras_html


def _error_box(msg: str) -> str:
    return f"""
    <div style='padding: 12px; border-radius: 8px; background: #FFF3E0;
                border-left: 5px solid #F57C00; color: #E65100;'>
        ⚠️ {msg}
    </div>
    """


def load_sample(sample_idx: int) -> str:
    """Quick-load a demo sample into the textarea."""
    if 0 <= sample_idx < len(SAMPLES):
        return SAMPLES[sample_idx]["text"]
    return ""


# --- Build the UI ---
def build_ui():
    with gr.Blocks(title="Phishing Detector — LLM-Powered",
                   theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 🛡️ AI-Powered Phishing Detector

        Paste a suspicious email or SMS below, pick a prompt strategy, and click **Analyze**.
        The LLM returns a verdict, confidence score, red flags, and a plain-English explanation.
        """)

        with gr.Row():
            with gr.Column(scale=2):
                input_text = gr.Textbox(
                    label="📥 Paste message here",
                    lines=12,
                    placeholder="From: ...\nSubject: ...\n\nBody...",
                )
                input_file = gr.File(
                    label="...or upload an .eml file",
                    file_types=[".eml"],
                )

                with gr.Row():
                    strategy_dd = gr.Dropdown(
                        choices=["cot", "few_shot", "zero_shot"],
                        value="cot",
                        label="Prompt strategy",
                        info="cot = Chain-of-Thought (best). few_shot uses 3 examples. zero_shot is the baseline.",
                    )
                    analyze_btn = gr.Button("🔍 Analyze", variant="primary", size="lg")

                if SAMPLES:
                    gr.Markdown("**Quick-load demo samples:**")
                    with gr.Row():
                        for i, sample in enumerate(SAMPLES):
                            name = sample.get("name", f"sample_{i}")
                            label_icon = "🚨" if sample.get("label") == 1 else "✅"
                            btn = gr.Button(f"{label_icon} {name}", size="sm")
                            btn.click(fn=lambda idx=i: load_sample(idx),
                                      outputs=input_text)

            with gr.Column(scale=2):
                verdict_html = gr.HTML(label="Verdict")
                gr.Markdown("### 🚩 Red flags detected")
                flags_html = gr.HTML()
                gr.Markdown("### 💬 Reasoning")
                reasoning_box = gr.Textbox(label="", lines=4, interactive=False)
                extras_html = gr.HTML()

        analyze_btn.click(
            fn=run_analysis,
            inputs=[input_text, strategy_dd, input_file],
            outputs=[verdict_html, flags_html, reasoning_box, extras_html],
        )

        gr.Markdown("""
        ---
        **About:** This is a team term project for LLM Cybersecurity.
        Compares Zero-shot vs Few-shot vs Chain-of-Thought prompting on a phishing detection task.
        See README.md for details.
        """)
    return demo


if __name__ == "__main__":
    ui = build_ui()
    ui.launch(server_port=GRADIO_PORT, share=GRADIO_SHARE)
