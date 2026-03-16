---
name: audio-transcription
description: "Use this skill when the user wants to transcribe audio or video files to text. Converts speech to text using Gemini 3 Flash AI — supports audio natively without external tools. Handles MP3, WAV, M4A, OGG, FLAC, AAC, WebM, MP4, MOV, AVI, MKV. Saves transcription as .txt file next to the original and returns the full text."
triggers: transcribe, transcription, audio to text, speech to text, convert audio, convert recording, voice to text, caption, subtitle, dictation, meeting notes, interview transcript
platform: all
---

# Audio Transcription Skill

AI-powered audio and video transcription using Gemini 3 Flash. Converts speech to accurate text. No external tools needed — Gemini accepts audio natively.

## How It Works

1. User provides an audio/video file path
2. File is read and base64-encoded in Electron
3. Sent to Gemini 3 Flash which processes audio natively
4. Gemini returns accurate transcription text
5. Transcription saved as `.txt` file next to the original
6. Genie speaks a summary to the user

## Tool

Use `transcribe_audio` with these parameters:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `path` | string | Yes | Full file path (supports `~`) |
| `language` | string | No | Language hint: "English", "Bengali", "Spanish", "French", etc. |
| `save_to_file` | boolean | No | Save as .txt file next to original. Default: `true` |

---

## Examples

**Basic transcription:**
```
transcribe_audio({ path: "~/Desktop/meeting_recording.mp3" })
```

**With language hint (improves accuracy):**
```
transcribe_audio({ path: "~/Downloads/interview.m4a", language: "Bengali" })
```

**Video file transcription:**
```
transcribe_audio({ path: "~/Desktop/lecture.mp4", language: "English" })
```

**Without saving to file:**
```
transcribe_audio({ path: "~/Desktop/memo.wav", save_to_file: false })
```

---

## Choosing When to Use Language Hint

| Scenario | Use Language Hint? |
|----------|-------------------|
| English audio | Optional — Gemini auto-detects well |
| Non-English audio | **Yes** — improves accuracy significantly |
| Mixed-language audio | Specify the primary language |
| Audio with accents | Specify the language for better results |
| Music/sound effects (not speech) | Don't use this tool — it's for speech only |

---

## Supported Formats

| Type | Extensions |
|------|-----------|
| **Audio** | MP3, WAV, M4A, OGG, FLAC, AAC, WMA, WebM |
| **Video** | MP4, MOV, AVI, MKV |

---

## Output Details

- **Transcription text** returned to genie (genie speaks a summary of the content)
- **Full text saved** as `{filename}_transcription.txt` next to the original file
- Preserves **speaker changes** and **paragraph structure** when detectable
- Clean, readable output — no timestamps by default

---

## Quality Tips

- **Provide language hint** for non-English audio — significantly improves accuracy
- **Clear audio** produces best results — minimal background noise is ideal
- **Single speaker** is more accurate than multi-speaker, but both work
- **File quality matters** — higher bitrate audio gives better transcription

---

## Limitations

- **Maximum 20MB per file** — Electron file reader limit. For larger files, user should split or compress first
- **Speech only** — designed for spoken content, not music transcription or sound effect identification
- **No real-time** — processes complete files, not live streams

---

## Avoid (Common Mistakes)

- **Don't transcribe huge files without warning** — files over 20MB will fail. Suggest splitting first.
- **Don't skip language hint for non-English** — accuracy drops significantly without it
- **Don't use for music** — this is speech-to-text, not music transcription
- **Don't forget the path** — `path` is required, always ask user for the file location

---

## Dependencies

- Gemini 3 Flash Preview — native audio processing (no Whisper or external ASR needed)
- Electron file reader — reads and base64-encodes audio files
