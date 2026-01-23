<p align="center">
  <img src="docs/images/logo.jpg" alt="BubbleVoice bot avatar" width="200"/>
</p>

# BubbleVoice 🎧

Telegram bot that converts voice messages into text using local Whisper and ffmpeg.
Supports a multilingual interface (EN / RU / UK).

---

## Features

- 🎙️ Voice message transcription
- 🌍 Multilingual interface (English / Русский / Українська)
- 🗣️ Language selection via /start and /language commands
- 🧠 Local Whisper model (no external APIs)
- 🔊 Audio conversion via ffmpeg (OGG/MP3/MP4 → WAV 16 kHz)
- ⚙️ Configurable via environment variables
- 📝 Structured logging

---

## Requirements

- Python 3.10+
- ffmpeg
- Telegram Bot Token

---

## Screenshots

<p align="center">
  <img src="docs/screenshots/language-selection.jpg" alt="Language selection" width="250"/>
  <img src="docs/screenshots/voice-transcription.jpg" alt="Voice transcription example" width="250"/>
</p>

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/machinatororis/telegram-voice2text-bot.git
cd telegram-voice2text-bot
```

### 2. Create virtual environment

```
python -m venv .venv
source .venv/bin/activate  # Linux / macOS
```
or
```
.venv\Scripts\activate     # Windows
```

### 3. Install dependencies

```
pip install -r requirements.txt
```

## Configuration (.env)

Create a ```.env``` file in the project root (it is ignored by git).

You can use ```.env.example``` as a starting point.

### Required variables
```
BOT_TOKEN=your_telegram_bot_token
```

### Optional variables
```
LOG_LEVEL=INFO
```

## FFMPEG_PATH (optional)

By default the app tries to run ```ffmpeg``` from the system ```PATH```.

If you deploy to a server or use a custom ffmpeg installation, you can manually specify the path to the executable:

### Linux:
```
FFMPEG_PATH=/usr/local/bin/ffmpeg
```

### Windows:
```
FFMPEG_PATH=C:\ffmpeg\bin\ffmpeg.exe
```
If ```FFMPEG_PATH``` is set but invalid, the app will fall back to searching ```ffmpeg``` in ```PATH```.

## Run the bot
```
python main.py
```
The `main.py` file is the application entry point and initializes
logging, configuration, and bot handlers.

## Notes

* ```.env``` is intentionally excluded from git.

* Use ```.env.example``` for reference.

* For server deployments, ```FFMPEG_PATH``` is recommended if ffmpeg is not in PATH.

