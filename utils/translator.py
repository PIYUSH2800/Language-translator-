import logging
from typing import Dict, Optional, Tuple
from googletrans import Translator, LANGUAGES

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class TranslatorService:
    """
    A service class wrapping googletrans functionality for language translation
    and detection. Implements clean error handling and status reporting.
    """
    
    def __init__(self):
        try:
            self.translator = Translator()
            logger.info("Googletrans Translator initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Translator: {e}")
            self.translator = None

    def get_supported_languages(self) -> Dict[str, str]:
        """
        Returns a sorted dictionary of supported languages.
        Key is language code, value is language name capitalized.
        """
        # Capitalize language names for better UI presentation
        return {code: name.capitalize() for code, name in LANGUAGES.items()}

    def get_lang_code(self, lang_name: str) -> Optional[str]:
        """
        Helper method to get language code from a capitalized language name.
        """
        if lang_name.lower() == "auto detect" or lang_name.lower() == "auto":
            return "auto"
            
        for code, name in LANGUAGES.items():
            if name.lower() == lang_name.lower():
                return code
        return None

    def get_lang_name(self, lang_code: str) -> str:
        """
        Helper method to get language name from a language code.
        """
        if lang_code == "auto":
            return "Auto Detect"
        return LANGUAGES.get(lang_code, lang_code).capitalize()

    def translate_text(
        self, text: str, src_lang: str, dest_lang: str
    ) -> Tuple[bool, str, str]:
        """
        Translates text from src_lang to dest_lang.
        
        Args:
            text: The string content to translate.
            src_lang: Code or name of the source language (e.g. 'en', 'spanish', 'auto').
            dest_lang: Code or name of the target language.
            
        Returns:
            Tuple[bool, str, str]: (Success status, Resulting text or Error message, Detected source language name)
        """
        if not text.strip():
            return False, "Input text is empty.", ""
            
        if not self.translator:
            # Try to re-initialize if it was previously failed
            try:
                self.translator = Translator()
            except Exception:
                return False, "Translation engine is offline/uninitialized. Check your internet connection.", ""

        # Resolve codes
        src_code = self.get_lang_code(src_lang) if len(src_lang) > 3 else src_lang
        dest_code = self.get_lang_code(dest_lang) if len(dest_lang) > 3 else dest_lang

        if not src_code:
            src_code = "auto"
        if not dest_code:
            dest_code = "en"

        try:
            # googletrans translate call
            result = self.translator.translate(text, src=src_code, dest=dest_code)
            
            # Detect source language
            detected_src_code = result.src
            detected_src_name = self.get_lang_name(detected_src_code)
            
            return True, result.text, detected_src_name
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return False, f"Translation Error: Could not connect to Google Translate services. Please check your internet connection and try again. Details: {str(e)}", ""

    def detect_language(self, text: str) -> Tuple[bool, str]:
        """
        Detects the language of a given text.
        
        Returns:
            Tuple[bool, str]: (Success status, Detected language name or Error message)
        """
        if not text.strip():
            return False, "Input text is empty."
            
        if not self.translator:
            try:
                self.translator = Translator()
            except Exception:
                return False, "Translation engine offline."

        try:
            detection = self.translator.detect(text)
            detected_name = self.get_lang_name(detection.lang)
            return True, detected_name
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return False, f"Detection Error: {str(e)}"
