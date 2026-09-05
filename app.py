from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
import webbrowser
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

import gradio as gr
from gradio_client import Client


APP_ROOT = Path(__file__).resolve().parent
SCRIPTS_DIR = APP_ROOT / "scripts"
OUTPUT_DIR = APP_ROOT / "generated_audio"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BACKEND_OPTIONS = {
    "Auto-detect live backend": "auto",
    "CustomVoice - built-in voices (8031)": "http://127.0.0.1:8031",
    "VoiceClone/Base - clone UI (8032)": "http://127.0.0.1:8032",
    "VoiceDesign - design UI (8033)": "http://127.0.0.1:8033",
}

MODE_INFO = {
    "custom": {
        "name": "CustomVoice",
        "url": "http://127.0.0.1:8031",
        "description": "Named Qwen speakers with instruction/style control.",
    },
    "clone": {
        "name": "VoiceClone / Base",
        "url": "http://127.0.0.1:8032",
        "description": "Reference-audio cloning plus save/load reusable voice prompts.",
    },
    "design": {
        "name": "VoiceDesign",
        "url": "http://127.0.0.1:8033",
        "description": "Create voices from natural-language descriptions.",
    },
}

BACKEND_ORDER = [
    url.strip().rstrip("/")
    for url in os.getenv(
        "DANDY_QWEN_BACKENDS",
        "http://127.0.0.1:8031,http://127.0.0.1:8032,http://127.0.0.1:8033",
    ).split(",")
    if url.strip()
]

for option_url in (
    "http://127.0.0.1:8031",
    "http://127.0.0.1:8032",
    "http://127.0.0.1:8033",
):
    if option_url not in BACKEND_ORDER:
        BACKEND_ORDER.append(option_url)

LANGUAGES = [
    "English",
    "Auto",
    "Chinese",
    "German",
    "Italian",
    "Portuguese",
    "Spanish",
    "Japanese",
    "Korean",
    "French",
    "Russian",
]

SPEAKERS = [
    "Ryan",
    "Aiden",
    "Uncle Fu",
    "Eric",
    "Dylan",
    "Vivian",
    "Serena",
    "Ono Anna",
    "Sohee",
]

VOICE_PRESETS = {
    "Phil candidate - Ryan": {
        "speaker": "Ryan",
        "instruction": "Warm American male voice, dry wit, relaxed podcast pacing, natural pauses, confident but not announcer-like.",
    },
    "Phil candidate - Aiden": {
        "speaker": "Aiden",
        "instruction": "Clear American male voice, thoughtful and friendly, conversational timing, light humor, steady midrange.",
    },
    "Jim candidate - Ryan": {
        "speaker": "Ryan",
        "instruction": "Dynamic American male voice, faster comedic timing, skeptical but warm, responsive conversational cadence.",
    },
    "Jim candidate - Eric": {
        "speaker": "Eric",
        "instruction": "Lively male voice, slightly raspy brightness, quick reactions, playful brotherly cadence.",
    },
    "Announcer candidate": {
        "speaker": "Ryan",
        "instruction": "Classic radio announcer delivery, clean articulation, upbeat but controlled, brief dramatic emphasis.",
    },
}


def _client(backend_url: str) -> Client:
    return Client(str(backend_url).strip().rstrip("/"))


def _normalize_url(backend_url: str) -> str:
    return str(backend_url or "").strip().rstrip("/")


def _backend_alive(backend_url: str) -> bool:
    backend_url = _normalize_url(backend_url)
    if not backend_url:
        return False
    try:
        with urlopen(backend_url, timeout=1.5) as response:
            return response.status < 500
    except (OSError, URLError, ValueError):
        return False


def _detect_backend() -> str:
    env_backend = _normalize_url(os.getenv("DANDY_QWEN_GRADIO_URL", ""))
    if env_backend and _backend_alive(env_backend):
        return env_backend

    for backend_url in BACKEND_ORDER:
        if _backend_alive(backend_url):
            return backend_url

    return env_backend or BACKEND_ORDER[0]


def _backend_kind(backend_url: str) -> str:
    backend_url = _normalize_url(backend_url)
    if backend_url.endswith(":8031"):
        return "custom"
    if backend_url.endswith(":8032"):
        return "clone"
    if backend_url.endswith(":8033"):
        return "design"
    return "unknown"


DEFAULT_BACKEND = _detect_backend()


def _copy_generated_audio(source: str, speaker: str) -> str:
    src = Path(source)
    if not src.exists():
        raise FileNotFoundError(f"Generated audio path does not exist: {src}")

    safe_speaker = "".join(ch.lower() if ch.isalnum() else "_" for ch in speaker).strip("_") or "voice"
    stamp = time.strftime("%Y%m%d_%H%M%S")
    target = OUTPUT_DIR / f"{stamp}_{safe_speaker}{src.suffix or '.wav'}"
    shutil.copyfile(src, target)
    return str(target)


def _extract_audio_path(result: Any) -> str:
    if isinstance(result, (list, tuple)) and result:
        first = result[0]
    else:
        first = result

    if isinstance(first, dict):
        path = first.get("path") or first.get("name")
    else:
        path = str(first) if first else ""

    if not path:
        raise RuntimeError(f"No audio path returned from Qwen backend: {result!r}")
    return path


def backend_status(backend_url: str) -> str:
    backend_url = _normalize_url(backend_url)
    if not _backend_alive(backend_url):
        live_backend = _detect_backend()
        if live_backend != backend_url and _backend_alive(live_backend):
            return f"No listener at {backend_url}. Live Qwen backend detected at {live_backend}."
        return f"No listener at {backend_url}."

    kind = _backend_kind(backend_url)
    if kind == "custom":
        return f"Connected to CustomVoice at {backend_url}. Dandy wrapper Generate is available."
    if kind == "clone":
        return f"Connected to VoiceClone/Base at {backend_url}. Open Native Qwen UI for cloning and saved voice prompts."
    if kind == "design":
        return f"Connected to VoiceDesign at {backend_url}. Open Native Qwen UI for voice design."
    return f"Connected to Qwen backend at {backend_url}."


def select_backend(mode: str):
    target = BACKEND_OPTIONS.get(mode, "auto")
    backend_url = _detect_backend() if target == "auto" else target
    return backend_url, backend_status(backend_url)


def apply_preset(preset: str):
    data = VOICE_PRESETS.get(preset) or {}
    return data.get("speaker", "Ryan"), data.get("instruction", "")


def _run_powershell(script_name: str, *args: str, timeout: int = 210) -> tuple[int, str]:
    script = SCRIPTS_DIR / script_name
    if not script.exists():
        return 1, f"Launcher script not found: {script}"

    command = [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script),
        *args,
    ]
    try:
        result = subprocess.run(
            command,
            cwd=str(APP_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return 1, f"Timed out waiting for {script_name}. Check logs in {APP_ROOT / 'logs'}."
    except Exception as exc:
        return 1, f"{type(exc).__name__}: {exc}"

    output = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part and part.strip())
    return result.returncode, output


def switch_mode(mode: str):
    info = MODE_INFO[mode]
    code, output = _run_powershell("Start-QwenTTSMode.ps1", "-Mode", mode)
    url = info["url"]
    if code != 0:
        return url, f"Failed to start {info['name']}.\n{output}"

    status = backend_status(url)
    if output:
        status = f"{status}\n\n{output}"
    return url, status


def stop_qwen_models():
    code, output = _run_powershell("Stop-QwenTTSModels.ps1", timeout=30)
    if code != 0:
        return f"Failed to stop Qwen model processes.\n{output}"
    return output or "Qwen model ports 8031-8033 are stopped."


def open_native_ui(backend_url: str):
    backend_url = _normalize_url(backend_url or _detect_backend())
    if not _backend_alive(backend_url):
        return f"No live Qwen UI at {backend_url}. Start a mode first."
    webbrowser.open(backend_url)
    return f"Opened native Qwen UI: {backend_url}"


def open_output_folder():
    try:
        os.startfile(OUTPUT_DIR)  # type: ignore[attr-defined]
        return f"Opened {OUTPUT_DIR}"
    except Exception as exc:
        return f"Could not open output folder: {type(exc).__name__}: {exc}"


def recent_outputs():
    rows = []
    files = sorted(
        [p for p in OUTPUT_DIR.iterdir() if p.is_file() and p.suffix.lower() in {".wav", ".mp3", ".flac", ".ogg"}],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )[:20]
    for path in files:
        stat = path.stat()
        rows.append(
            [
                path.name,
                round(stat.st_size / 1024, 1),
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)),
            ]
        )
    return rows


def synthesize(
    text: str,
    language: str,
    speaker: str,
    instruction: str,
    backend_url: str,
):
    text = (text or "").strip()
    if not text:
        return None, "", "Text is required."

    backend_url = _normalize_url(backend_url or _detect_backend())
    kind = _backend_kind(backend_url)

    if not _backend_alive(backend_url):
        live_backend = _detect_backend()
        if live_backend != backend_url and _backend_alive(live_backend):
            return None, "", f"No listener at {backend_url}. Live Qwen backend detected at {live_backend}."
        return None, "", f"No listener at {backend_url}."

    if kind == "clone":
        return None, "", f"VoiceClone/Base is live at {backend_url}. Use Open Native Qwen UI for cloning and cloned-voice generation."

    if kind == "design":
        return None, "", f"VoiceDesign is live at {backend_url}. Use Open Native Qwen UI for voice design generation."

    try:
        client = _client(backend_url)
        result = client.predict(
            text=text,
            lang_disp=language or "English",
            spk_disp=speaker or "Ryan",
            instruct=(instruction or "").strip(),
            api_name="/run_instruct",
        )
        generated_path = _extract_audio_path(result)
        saved_path = _copy_generated_audio(generated_path, speaker or "voice")
        status = {
            "backend": backend_url,
            "speaker": speaker,
            "language": language,
            "saved_audio": saved_path,
            "raw_backend_result": result,
        }
        return saved_path, saved_path, json.dumps(status, indent=2)
    except Exception as exc:
        return None, "", f"{type(exc).__name__}: {exc}"


CSS = """
.gradio-container { max-width: none !important; }
#status_box textarea { font-family: Consolas, monospace; font-size: 12px; }
"""


with gr.Blocks(title="Dandy Qwen TTS") as demo:
    gr.Markdown("# Dandy Qwen TTS")
    gr.Markdown("Windows-native operator console for the local Qwen3-TTS stack.")

    with gr.Row():
        backend_mode = gr.Dropdown(
            label="Backend",
            choices=list(BACKEND_OPTIONS.keys()),
            value="Auto-detect live backend",
            scale=2,
        )
        backend = gr.Textbox(label="Active Qwen URL", value=DEFAULT_BACKEND, scale=3)
        check = gr.Button("Check", scale=1)

    with gr.Row():
        start_custom = gr.Button("Start CustomVoice", variant="primary")
        start_clone = gr.Button("Start Voice Clone")
        start_design = gr.Button("Start Voice Design")
        open_native = gr.Button("Open Native Qwen UI")
        stop_models = gr.Button("Stop Qwen Models", variant="stop")

    status = gr.Textbox(label="Backend / launcher status", lines=5, elem_id="status_box")

    with gr.Tabs():
        with gr.Tab("Dandy CustomVoice"):
            with gr.Row():
                with gr.Column(scale=2):
                    text = gr.Textbox(
                        label="Text",
                        lines=8,
                        value="Welcome back to the Phil and Jim Dandy Show. Today we are testing the new Qwen voices.",
                    )
                    preset = gr.Dropdown(
                        label="Voice preset",
                        choices=list(VOICE_PRESETS.keys()),
                        value="Phil candidate - Ryan",
                    )
                    with gr.Row():
                        language = gr.Dropdown(label="Language", choices=LANGUAGES, value="English")
                        speaker = gr.Dropdown(label="Speaker", choices=SPEAKERS, value="Ryan")
                    instruction = gr.Textbox(
                        label="Instruction / style",
                        lines=3,
                        value=VOICE_PRESETS["Phil candidate - Ryan"]["instruction"],
                    )
                    generate = gr.Button("Generate", variant="primary")

                with gr.Column(scale=2):
                    audio = gr.Audio(label="Generated audio", type="filepath", autoplay=True)
                    saved_path = gr.Textbox(label="Saved file")
                    detail = gr.Textbox(label="Result detail", lines=10, elem_id="status_box")

        with gr.Tab("Recent Audio"):
            recent = gr.Dataframe(
                headers=["File", "KB", "Modified"],
                datatype=["str", "number", "str"],
                value=recent_outputs(),
                interactive=False,
                label="Last 20 generated files",
            )
            with gr.Row():
                refresh_recent = gr.Button("Refresh")
                open_folder = gr.Button("Open generated_audio Folder")
            folder_status = gr.Textbox(label="Folder status", lines=1)

        with gr.Tab("Mode Guide"):
            gr.Markdown(
                """
### CustomVoice
Named Qwen speakers such as Ryan, Aiden, Vivian, Eric and others, with instruction/style control. The Dandy Generate panel talks directly to this mode.

### Voice Clone / Base
Use reference audio to clone a voice. The native Qwen UI includes immediate clone-and-generate plus save/load reusable voice prompts.

### VoiceDesign
Describe a voice in natural language and generate speech with that designed voice.

Only one heavy Qwen model should be loaded at a time on this machine. Starting another mode stops the current Qwen model first; the Dandy operator UI remains running.
"""
            )

    backend_mode.change(select_backend, inputs=[backend_mode], outputs=[backend, status])
    check.click(backend_status, inputs=[backend], outputs=[status])

    start_custom.click(lambda: switch_mode("custom"), outputs=[backend, status])
    start_clone.click(lambda: switch_mode("clone"), outputs=[backend, status])
    start_design.click(lambda: switch_mode("design"), outputs=[backend, status])
    open_native.click(open_native_ui, inputs=[backend], outputs=[status])
    stop_models.click(stop_qwen_models, outputs=[status])

    preset.change(apply_preset, inputs=[preset], outputs=[speaker, instruction])
    generate.click(
        synthesize,
        inputs=[text, language, speaker, instruction, backend],
        outputs=[audio, saved_path, detail],
    )

    refresh_recent.click(recent_outputs, outputs=[recent])
    open_folder.click(open_output_folder, outputs=[folder_status])


if __name__ == "__main__":
    demo.queue(default_concurrency_limit=1).launch(
        server_name=os.getenv("DANDY_QWEN_UI_HOST", "127.0.0.1"),
        server_port=int(os.getenv("DANDY_QWEN_UI_PORT", "7861")),
        share=False,
        pwa=True,
        theme=gr.themes.Soft(),
        css=CSS,
    )
