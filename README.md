# Dandy Qwen TTS Package

Windows-native local operator package for Qwen3-TTS.

## One-click start

Run:

```bat
start_dandy_qwen_tts_ui.cmd
```

This starts the default `CustomVoice` Qwen backend, starts the Dandy operator UI, and opens:

```text
http://127.0.0.1:7861
```

If the selected Qwen backend or operator UI is already running, the launcher reuses it instead of starting a duplicate.

## Dandy operator UI

The operator UI now provides:

- CustomVoice generation with named Qwen speakers and style/instruction prompts.
- One-click switching between CustomVoice, VoiceClone/Base, and VoiceDesign.
- Automatic one-heavy-model-at-a-time handling for the RTX 3050.
- Open Native Qwen UI control for the active backend.
- Stop Qwen Models control.
- Recent generated-audio view and direct access to the `generated_audio` folder.
- Backend discovery/status reporting.
- Gradio PWA support.

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

Reference-audio cloning, immediate clone-and-generate, and reusable saved voice prompts through the native Qwen UI.

Manual launcher:

```bat
start_voice_clone.cmd
```

### VoiceDesign

```text
http://127.0.0.1:8033
```

Natural-language voice design through the native Qwen UI.

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
