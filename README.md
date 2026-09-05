# Dandy Qwen TTS Package

Windows-native local operator package for Qwen3-TTS.

## One-click start

Run:

```bat
start_dandy_qwen_tts_ui.cmd
```

This starts the default `CustomVoice` Qwen backend, starts the unified Dandy Qwen TTS Studio, and opens:

```text
http://127.0.0.1:7861
```

If the selected Qwen backend or operator UI is already running, the launcher reuses it instead of starting a duplicate.

## Unified tabbed studio

The browser stays on the Dandy studio at port `7861`. The native Qwen Gradio workbenches are embedded as tabs instead of opening separate browser pages.

Tabs:

- `Dandy CustomVoice` — Dandy's fast CustomVoice wrapper.
- `Qwen CustomVoice Native` — the complete upstream Qwen CustomVoice Gradio interface.
- `Voice Clone` — the complete Qwen Base/VoiceClone interface.
- `VoiceDesign` — the complete Qwen VoiceDesign interface.
- `Tools & Audio` — generated-audio browser, file/folder access, microphone/upload handoff, and Audacity launch/open support.

Selecting a model tab automatically switches the single heavy Qwen model. This preserves the one-model-at-a-time requirement for the RTX 3050 while keeping all navigation inside one browser UI.

## Voice cloning

The embedded `Voice Clone` tab uses Qwen's native Base-model workflow. It includes:

- Reference Audio input.
- Microphone recording.
- Audio-file upload / drag-and-drop.
- Reference transcript input.
- Optional x-vector-only mode.
- Clone & Generate.
- Save reusable voice prompt files.
- Load saved voice prompt files and generate new speech.

For best cloning quality, use a clean short reference clip and provide the exact spoken transcript when possible.

## Audacity handoff

The `Tools & Audio` tab can launch Audacity and can open an uploaded or freshly recorded audio clip in Audacity for cleanup/editing.

Audacity lookup order:

1. `DANDY_AUDACITY` environment variable.
2. `audacity.exe` / `audacity` available on `PATH`.
3. Standard Windows Audacity install locations.

Generated files remain in the local `generated_audio` directory and are excluded from Git.

## Qwen modes

### CustomVoice

```text
http://127.0.0.1:8031
```

Named Qwen speakers with instruction/style control.

Manual launcher:

```bat
start_custom_voice.cmd
```

### VoiceClone / Base

```text
http://127.0.0.1:8032
```

Reference-audio cloning, immediate clone-and-generate, and reusable saved voice prompts.

Manual launcher:

```bat
start_voice_clone.cmd
```

### VoiceDesign

```text
http://127.0.0.1:8033
```

Natural-language voice design.

Manual launcher:

```bat
start_voice_design.cmd
```

### Stop loaded Qwen models

```bat
stop_qwen_tts_models.cmd
```

Only one heavy Qwen model should be loaded at a time on the RTX 3050.

## Current runtime paths

Qwen engine:

```text
R:\Services\qwen_engine
```

Python 3.12 environment:

```text
R:\Services\qwen_tts_312
```

Python executable:

```text
R:\Services\qwen_tts_312\Scripts\python.exe
```

The launch scripts also accept environment overrides:

- `DANDY_QWEN_ENGINE`
- `DANDY_QWEN_VENV`
- `DANDY_QWEN_PYTHON`
- `DANDY_AUDACITY`

## Local package paths

Repository:

```text
C:\Users\bryan\Desktop\dandy_qwen_tts_ui
```

Generated audio:

```text
C:\Users\bryan\Desktop\dandy_qwen_tts_ui\generated_audio
```

Logs:

```text
C:\Users\bryan\Desktop\dandy_qwen_tts_ui\logs
```

Generated audio, logs, staging data, caches, and probe files are intentionally excluded from Git.

## Production bridge

The recovered package also contains the Dandy Show bridge on port `8020`. Its historical Dandy Show/FFmpeg paths have not yet been modernized because the current Dandy Show root has not been identified. The UI/Qwen launcher does not depend on the production bridge.
