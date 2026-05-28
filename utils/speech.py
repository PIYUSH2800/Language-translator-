import os
import tempfile
import logging
import threading
from typing import Callable, Optional

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

import speech_recognition as sr
from gtts import gTTS
import pyttsx3

# Configure logging
logger = logging.getLogger(__name__)

class SpeechService:
    """
    Manages speech input (Voice Recognition) and speech output (Text-To-Speech)
    using gTTS, pygame, and pyttsx3 for offline fallback.
    """

    def __init__(self):
        self.tts_lock = threading.Lock()
        self.is_playing_tts = False
        
        # Initialize pygame mixer for audio playback
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init()
                logger.info("Pygame mixer initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Pygame mixer: {e}")

        # Keep track of active temp files to clean them up
        self.temp_files = []

    def clean_temp_files(self):
        """Attempts to delete any temporary audio files created during TTS."""
        # Unload mixer music first to release locks
        try:
            if PYGAME_AVAILABLE and pygame.mixer.get_init():
                pygame.mixer.music.unload()
        except Exception:
            pass

        for filepath in list(self.temp_files):
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    self.temp_files.remove(filepath)
                except Exception as e:
                    logger.debug(f"Could not delete temp file {filepath}: {e}")

    def speak_text(
        self, text: str, lang_code: str, status_callback: Callable[[str], None]
    ):
        """
        Synthesizes text to speech. Tries gTTS (online) first, 
        and falls back to pyttsx3 (offline) if internet or gTTS fails.
        """
        # Ensure only one TTS plays at a time
        with self.tts_lock:
            self.is_playing_tts = True
            
            # Auto-detect lang code or normalize it
            if not lang_code or lang_code == "auto":
                lang_code = "en"
            
            # Simple clean of previous audio files
            self.clean_temp_files()

            success = False
            
            # 1. Try gTTS if pygame is available
            if PYGAME_AVAILABLE:
                status_callback("Generating speech (online)...")
                try:
                    tts = gTTS(text=text, lang=lang_code, slow=False)
                    
                    # Write to temp file
                    fd, temp_path = tempfile.mkstemp(suffix=".mp3")
                    os.close(fd) # Close file descriptor so pygame can write/read it
                    
                    tts.save(temp_path)
                    self.temp_files.append(temp_path)
                    
                    # Play using Pygame
                    if not pygame.mixer.get_init():
                        pygame.mixer.init()
                    
                    status_callback("Speaking (gTTS)...")
                    pygame.mixer.music.load(temp_path)
                    pygame.mixer.music.play()
                    
                    # Block thread until done playing or stopped
                    while pygame.mixer.music.get_busy() and self.is_playing_tts:
                        pygame.time.Clock().tick(10)
                    
                    pygame.mixer.music.unload()
                    success = True
                    
                except Exception as e:
                    logger.warning(f"gTTS or Pygame playback failed, trying pyttsx3 fallback: {e}")
            else:
                logger.info("Pygame not available. Bypassing online gTTS playback.")
                
            # 2. Offline Fallback using pyttsx3
            if not success and self.is_playing_tts:
                status_callback("Speaking (Offline Engine)...")
                try:
                    # Run pyttsx3 fully within the background thread
                    engine = pyttsx3.init()
                    
                    # Try to configure language/voice matching lang_code
                    voices = engine.getProperty("voices")
                    
                    # Attempt to find a voice that contains the requested language code
                    selected_voice = None
                    for voice in voices:
                        # Language code match (e.g. 'en', 'es', 'fr') in voice languages or name
                        if voice.languages and any(lang_code.lower() in lang.lower() for lang in voice.languages):
                            selected_voice = voice.id
                            break
                        elif lang_code.lower() in voice.name.lower():
                            selected_voice = voice.id
                            break
                            
                    if selected_voice:
                        engine.setProperty("voice", selected_voice)
                        
                    engine.setProperty("rate", 150)  # Moderate speed
                    engine.say(text)
                    engine.runAndWait()
                    
                    # Stop pyttsx3 engine safely
                    engine.stop()
                    success = True
                except Exception as pyttsx3_err:
                    logger.error(f"pyttsx3 playback failed: {pyttsx3_err}")
                    status_callback("Speech playback error.")
            
            if success and self.is_playing_tts:
                status_callback("Speech finished.")
            elif not self.is_playing_tts:
                status_callback("Speech stopped.")
                
            self.is_playing_tts = False
            self.clean_temp_files()

    def stop_speaking(self):
        """Stops any active TTS audio playback."""
        self.is_playing_tts = False
        try:
            if PYGAME_AVAILABLE and pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
        except Exception as e:
            logger.error(f"Error stopping pygame mixer: {e}")

    def recognize_speech(
        self, 
        lang_code: str, 
        status_callback: Callable[[str], None], 
        success_callback: Callable[[str], None]
    ):
        """
        Records sound from the microphone and attempts to transcribe it.
        Uses speech_recognition + Google Speech API.
        """
        if not lang_code or lang_code == "auto":
            lang_code = "en-US" # Default to English speech recognition
            
        recognizer = sr.Recognizer()
        
        status_callback("Initializing microphone...")
        try:
            with sr.Microphone() as source:
                status_callback("Adjusting for background noise...")
                # Allow a brief adjustment for noise
                recognizer.adjust_for_ambient_noise(source, duration=0.8)
                
                status_callback("Listening... Speak now!")
                # Listen with timeout parameters
                audio = recognizer.listen(source, timeout=8, phrase_time_limit=12)
                
                status_callback("Transcribing speech...")
                # Call Google Speech API
                text = recognizer.recognize_google(audio, language=lang_code)
                
                status_callback("Voice input captured!")
                success_callback(text)
                
        except sr.WaitTimeoutError:
            logger.info("Speech recognition timed out waiting for input.")
            status_callback("Error: Listening timed out. No speech detected.")
        except sr.UnknownValueError:
            logger.info("Speech recognition could not understand audio.")
            status_callback("Error: Speech not recognized. Speak clearly.")
        except sr.RequestError as e:
            logger.error(f"Could not request results from Google Speech Recognition service: {e}")
            status_callback("Error: Transcription service unavailable. Check internet.")
        except OSError as e:
            logger.error(f"Microphone access error: {e}")
            status_callback("Error: Microphone not found or permission denied.")
        except Exception as e:
            logger.error(f"Unexpected error in speech recognition: {e}")
            status_callback(f"Error: {str(e)}")
