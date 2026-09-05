from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path

import gradio as gr

import app as core


APP_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = APP_ROOT / "generated_audio"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

NATIVE_URLS = {
    "custom": "http://127.0.0.1:8031",
    "clone": "http://127.0.0.1:8032",
    "design": "http://127.0.0.1:8033",
}

CSS = """
html, body {
    background: #07111f !important;
}
.gradio-container {
    max-width: none !important;
    min-height: 100vh;
    background:
        radial-gradient(circle at 15% 0%, rgba(0, 205, 255, .16), transparent 30%),
        radial-gradient(circle at 90% 5%, rgba(104, 76, 255, .16), transparent 28%),
        linear-gradient(180deg, #081421 0%, #0b1624 48%, #09111c 100%) !important;
}
.dandy-hero {
    margin: 2px 0 14px 0;
    padding: 22px 26px;
    border: 1px solid rgba(72, 211, 255, .32);
    border-radius: 16px;
    background: linear-gradient(120deg, rgba(0, 185, 235, .16), rgba(67, 52, 180, .18));
    box-shadow: 0 14px 40px rgba(0, 0, 0, .26);
}
.dandy-hero h1 {
    margin: 2px 0 4px 0 !important;
    color: #f4fbff !important;
    font-size: 2.1rem !important;
    letter-spacing: .01em;
}
.dandy-hero p {
    color: #b8cbda !important;
    margin: 0 !important;
}
.dandy-kicker {
    color: #51dcff;
    font-size: .76rem;
    font-weight: 800;
    letter-spacing: .16em;
}
button[role="tab"] {
    border-radius: 10px 10px 0 0 !important;
    border: 1px solid rgba(123, 165, 196, .28) !important;
    background: linear-gradient(180deg, #17283a, #101e2d) !important;
    color: #b9cad8 !important;
    font-weight: 750 !important;
    padding: 12px 16px !important;
    margin-right: 4px !important;
}
button[role="tab"]:hover {
    color: #ffffff !important;
    border-color: rgba(71, 214, 255, .7) !important;
    transform: translateY(-1px);
}
button[role="tab"][aria-selected="true"] {
    color: #07111f !important;
    background: linear-gradient(90deg, #4be0ff, #78b8ff) !important;
    border-color: #80e9ff !important;
    box-shadow: 0 0 22px rgba(61, 215, 255, .28);
}
#check_btn {
    background: linear-gradient(90deg, #1688c8, #36b7dc) !important;
    color: white !important;
    border: none !important;
}
#generate_btn {
    background: linear-gradient(90deg, #00b9dc, #437cf6) !important;
    color: white !important;
    border: none !important;
    font-weight: 800 !important;
}
#stop_btn {
    background: linear-gradient(90deg, #b62f52, #e34b62) !important;
    color: white !important;
    border: none !important;
}
#status_box textarea {
    font-family: Consolas, monospace;
    font-size: 12px;
}
.native-frame {
    width: 100%;
    height: 76vh;
    min-height: 720px;
    border: 1px solid rgba(82, 220, 255, .36);
    border-radius: 12px;
    background: white;
    box-shadow: 0 14px 34px rgba(0, 0, 0, .3);
}
"""


def iframe_html(url: str, label: str) -> str:
    stamp = int(time.time())
    return (
        f'<iframe class="native-frame" title="{label}" '
        f'src="{url}?dandy_embed={stamp}" '
        'allow="microphone; clipboard-read; clipboard-write" '
        'loading="eager"></iframe>'
    )


def blank_frame(label: str) -> str:
    return (
        '<div style="padding:28px;border:1px solid rgba(72,211,255,.35);border-radius:12px;min-height:180px;'
        'background:linear-gradient(135deg,#102337,#151c35);color:#d8e9f4">'
        f'<h3 style="color:#5ee4ff">{label}</h3>'
        '<p>Select this tab to start the required Qwen model and load its native Gradio interface here.</p>'
        '</div>'
    )


def switch_and_embed(mode: str):
    url, status = core.switch_mode(mode)
    if core._backend_alive(url):
        return url, status, iframe_html(url, core.MODE_INFO[mode]["name"])
    return url, status, blank_frame(f"{core.MODE_INFO[mode]['name']} is not ready")


def switch_custom_only():
    url, status = core.switch_mode("custom")
    return url, status


def reload_native(mode: str):
    url = NATIVE_URLS[mode]
    if not core._backend_alive(url):
        return blank_frame(f"{core.MODE_INFO[mode]['name']} is not running"), f"No listener at {url}."
    return iframe_html(url, core.MODE_INFO[mode]["name"]), f"Reloaded embedded {core.MODE_INFO[mode]['name']} UI."


def find_audacity() -> str | None:
    explicit = os.getenv("DANDY_AUDACITY", "").strip()
    candidates = [
        explicit,
        shutil.which("audacity.exe") or "",
        shutil.which("audacity") or "",
        r"C:\Program Files\Audacity\Audacity.exe",
        r"C:\Program Files (x86)\Audacity\Audacity.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def launch_audacity(audio_path: str | None = None) -> str:
    exe = find_audacity()
    if not exe:
        return "Audacity was not found. Install it or set DANDY_AUDACITY to Audacity.exe."
    args = [exe]
    if audio_path:
        path = Path(audio_path)
        if path.exists():
            args.append(str(path))
    try:
        subprocess.Popen(args, cwd=str(APP_ROOT))
        if len(args) > 1:
            return f"Opened in Audacity: {args[1]}"
        return f"Opened Audacity: {exe}"
    except Exception as exc:
        return f"Could not launch Audacity: {type(exc).__name__}: {exc}"


def recent_outputs():
    return core.recent_outputs()


with gr.Blocks(title="Dandy Qwen TTS Studio") as demo:
    gr.HTML(
        """
<div class="dandy-hero">
  <div class="dandy-kicker">WINDOWS-NATIVE • LOCAL QWEN3-TTS • DANDY AUDIO LAB</div>
  <h1>Dandy Qwen TTS Studio</h1>
  <p>One operator shell for CustomVoice, Voice Clone, VoiceDesign, recording, generated audio and Audacity handoff.</p>
</div>
"""
    )

    with gr.Row():
        backend = gr.Textbox(label="Active Qwen URL", value=core.DEFAULT_BACKEND, scale=3)
        check = gr.Button("Check Backend", scale=1, elem_id="check_btn")
        stop_models = gr.Button("Stop Qwen Models", variant="stop", scale=1, elem_id="stop_btn")

    status = gr.Textbox(label="Backend / launcher status", lines=5, elem_id="status_box")

    with gr.Tabs():
        with gr.Tab("Dandy CustomVoice", id="dandy-custom") as dandy_tab:
            gr.Markdown("Dandy's fast CustomVoice wrapper. Returning to this tab automatically restores the CustomVoice model.")
            with gr.Row():
                with gr.Column(scale=2):
                    text = gr.Textbox(
                        label="Text",
                        lines=8,
                        value="Welcome back to the Phil and Jim Dandy Show. Today we are testing the new Qwen voices.",
                    )
                    preset = gr.Dropdown(
                        label="Voice preset",
                        choices=list(core.VOICE_PRESETS.keys()),
                        value="Phil candidate - Ryan",
                    )
                    with gr.Row():
                        language = gr.Dropdown(label="Language", choices=core.LANGUAGES, value="English")
                        speaker = gr.Dropdown(label="Speaker", choices=core.SPEAKERS, value="Ryan")
                    instruction = gr.Textbox(
                        label="Instruction / style",
                        lines=3,
                        value=core.VOICE_PRESETS["Phil candidate - Ryan"]["instruction"],
                    )
                    generate = gr.Button("Generate", variant="primary", elem_id="generate_btn")

                with gr.Column(scale=2):
                    audio = gr.Audio(label="Generated audio", type="filepath", autoplay=True)
                    saved_path = gr.Textbox(label="Saved file")
                    detail = gr.Textbox(label="Result detail", lines=10, elem_id="status_box")

        with gr.Tab("Qwen CustomVoice Native", id="qwen-custom") as qwen_custom_tab:
            gr.Markdown("Full upstream Qwen CustomVoice Gradio page, embedded here.")
            custom_reload = gr.Button("Reload Embedded CustomVoice UI")
            custom_frame = gr.HTML(blank_frame("Qwen CustomVoice Native"))

        with gr.Tab("Voice Clone", id="qwen-clone") as clone_tab:
            gr.Markdown(
                "Full Qwen Base / VoiceClone workbench. Its Reference Audio control supports microphone recording and file upload/drop, "
                "plus Clone & Generate and Save / Load Voice workflows."
            )
            clone_reload = gr.Button("Reload Embedded Voice Clone UI")
            clone_frame = gr.HTML(blank_frame("Qwen Voice Clone / Base"))

        with gr.Tab("VoiceDesign", id="qwen-design") as design_tab:
            gr.Markdown("Full Qwen VoiceDesign workbench for natural-language voice creation.")
            design_reload = gr.Button("Reload Embedded VoiceDesign UI")
            design_frame = gr.HTML(blank_frame("Qwen VoiceDesign"))

        with gr.Tab("Tools & Audio", id="tools"):
            gr.Markdown("### Generated audio and external editor handoff")
            recent = gr.Dataframe(
                headers=["File", "KB", "Modified"],
                datatype=["str", "number", "str"],
                value=recent_outputs(),
                interactive=False,
                label="Last 20 generated files",
            )
            with gr.Row():
                refresh_recent = gr.Button("Refresh Audio List")
                open_folder = gr.Button("Open generated_audio Folder")
                launch_audacity_button = gr.Button("Launch Audacity")
            tools_status = gr.Textbox(label="Tools status", lines=2)
            audacity_audio = gr.Audio(
                label="Drop an audio file here or record from microphone, then Open in Audacity",
                type="filepath",
                sources=["upload", "microphone"],
            )
            open_in_audacity = gr.Button("Open This Audio in Audacity")

    check.click(core.backend_status, inputs=[backend], outputs=[status])
    stop_models.click(core.stop_qwen_models, outputs=[status])

    preset.change(core.apply_preset, inputs=[preset], outputs=[speaker, instruction])
    generate.click(
        core.synthesize,
        inputs=[text, language, speaker, instruction, backend],
        outputs=[audio, saved_path, detail],
    )

    dandy_tab.select(switch_custom_only, outputs=[backend, status])
    qwen_custom_tab.select(lambda: switch_and_embed("custom"), outputs=[backend, status, custom_frame])
    clone_tab.select(lambda: switch_and_embed("clone"), outputs=[backend, status, clone_frame])
    design_tab.select(lambda: switch_and_embed("design"), outputs=[backend, status, design_frame])

    custom_reload.click(lambda: reload_native("custom"), outputs=[custom_frame, status])
    clone_reload.click(lambda: reload_native("clone"), outputs=[clone_frame, status])
    design_reload.click(lambda: reload_native("design"), outputs=[design_frame, status])

    refresh_recent.click(recent_outputs, outputs=[recent])
    open_folder.click(core.open_output_folder, outputs=[tools_status])
    launch_audacity_button.click(lambda: launch_audacity(None), outputs=[tools_status])
    open_in_audacity.click(launch_audacity, inputs=[audacity_audio], outputs=[tools_status])


if __name__ == "__main__":
    demo.queue(default_concurrency_limit=1).launch(
        server_name=os.getenv("DANDY_QWEN_UI_HOST", "127.0.0.1"),
        server_port=int(os.getenv("DANDY_QWEN_UI_PORT", "7861")),
        share=False,
        pwa=True,
        theme=gr.themes.Soft(),
        css=CSS,
    )
