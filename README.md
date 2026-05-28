<<<<<<< HEAD
# LingoFlux Translator

A feature-rich, production-ready desktop Translation Application built with Python using `Tkinter` (with a responsive, dark/light design system), wrapping `googletrans` for translations, `speech_recognition` for microphone voice input, and a combination of `gTTS` and `pyttsx3` for premium online & offline text-to-speech feedback.

---

## Features

1. **Robust Translations**: Translates words, phrases, and long paragraphs across more than 100 languages.
2. **Auto Language Detection**: Detects the language of the entered text dynamically.
3. **Voice Input (STT)**: Speak into your microphone to record and transcribe text directly.
4. **Text-To-Speech (TTS)**: Listen to both input text and translated output.
   - *Online Mode (Premium Quality)*: Uses Google Text-to-Speech (`gTTS`) and `pygame` for smooth playback.
   - *Offline Fallback*: Automatically falls back to the native offline `pyttsx3` speech engine if you lose internet.
5. **Real-time Translation**: Debounced translate-while-typing mode so you get immediate translations without API spam.
6. **Theme Switcher**: Toggle smoothly between dark and light mode.
7. **Copy & Swap**: Copy translation instantly to clipboard and swap source/target texts and languages in one click.
8. **Translation History**: A built-in history modal where you can view past translations and restore them.
9. **Export Feature**: Save translation projects directly to text files.
10. **Responsive & Non-Freezing UI**: Runs translation, TTS, and STT operations in background threads to keep the user interface responsive and fluent.

---

## Project Structure

```text
python_language_translator/
│
├── main.py                    # Main app entry point & UI implementation
├── requirements.txt           # Package dependencies
├── README.md                  # Documentation and guide
└── utils/                     
    ├── __init__.py            
    ├── translator.py          # googletrans API service wrapper
    ├── speech.py              # Voice-to-text and Text-to-voice engines
    └── ui_helpers.py          # Custom styles, themes, and UI widgets
```

---

## Installation

### Prerequisites
- Python 3.7 or higher installed on your system.
- An active internet connection (required for translation API and high-quality voice features).

### 1. Install Dependencies
Run the command below to install all requirements:
```bash
pip install googletrans==4.0.0-rc1 SpeechRecognition gTTS pygame pyttsx3 PyAudio legacy-cgi
```

#### Note on Python 3.13+
Since the `cgi` library was removed in Python 3.13, you *must* install `legacy-cgi` for `googletrans` dependencies (`httpx`) to work correctly:
```bash
pip install legacy-cgi
```

#### Troubleshooting PyAudio Installation on Windows
If you run into issues installing `PyAudio` via pip, you can use the pre-compiled wheel installer:
```bash
pip install pipwin
pipwin install pyaudio
```
Alternatively, download the wheel corresponding to your python version from [Unofficial Windows Binaries for Python Extension Packages](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio) and install it:
```bash
pip install PyAudio-x.x.x-cpXX-cpXX-win_amd64.whl
```

---

## How to Run

Navigate to the project directory and execute:
```bash
python main.py
```

---

## Shortcuts & Controls

The app includes various keyboard shortcuts for speed and productivity:

| Shortcut | Description |
|---|---|
| `Ctrl + Return` | Translate source text instantly |
| `Ctrl + T` | Toggle between Dark and Light mode themes |
| `Ctrl + L` | Start voice recognition (mic listening) |
| `Ctrl + S` | Listen to output translated text |
| `Ctrl + H` | View/Open translation history log |

---

## Error Handling

- **Connection Drops**: If the translator cannot reach the server, the status bar will turn red indicating network failure. The interface will not freeze, and it lets you retry cleanly.
- **Audio Device Errors**: If no mic is connected, the voice button notifies you via status with a warning and prevents crashing.
- **Speech Engine Lock**: Restores system resources gracefully if window is closed during audio playback.
=======
# Language-translator-
this project is made in python language using googletrans &amp; tkinter 
>>>>>>> 7f1c7b2bc5f152705edfdf1c595b259e73da32ba
