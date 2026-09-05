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
.gradio-container { max-width: none !important; }
#status_box textarea { font-family: Consolas, monospace; font-size: 12px; }
.native-frame { width: 100%; height: 76vh; min-height: 720px; border: 1px solid var(--border-color-primary); border-radius: 10px; background: white; }
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
        '<div style="padding:28px;border:1px solid #999;border-radius:10px;min-height:180px">'
        f'<h3>{label}</h3><p>Select this tab to start the required Qwen model and load its native Gradio interface here.</p>'
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
    gr.Markdown("# Dandy Qwen TTS Studio")
    gr.Markdown(
        "One Windows-native shell for Dandy controls plus the three native Qwen3-TTS Gradio workbenches. "
        "Only one heavy Qwen model is kept loaded at a time."
    )

    with gr.Row():
        backend = gr.Textbox(label="Active Qwen URL", value=core.DEFAULT_BACKEND, scale=3)
        check = gr.Button("Check Backend", scale=1)
        stop_models = gr.Button("Stop Qwen Models", variant="stop", scale=1)

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
                    generate = gr.Button("Generate", variant="primary")

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
                label="Drop an audio file here, then Open in Audacity",
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

    # Tab navigation owns the heavy-model swap.
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
