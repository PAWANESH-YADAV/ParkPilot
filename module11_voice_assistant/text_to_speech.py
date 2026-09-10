"""
Module 11 — Text-to-Speech (TTS)
==================================
Converts text responses to speech audio using gTTS (Google Text-to-Speech).
Falls back to pyttsx3 (offline) when gTTS is unavailable.

Dependencies (optional):
    pip install gTTS playsound pyttsx3

Usage:
    from module11_voice_assistant.text_to_speech import TextToSpeech
    tts = TextToSpeech(language="en")
    tts.speak("Slot A3 is available. Please proceed to Zone A.")
"""

import os
import io
import logging
import tempfile
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    logger.warning("gTTS not installed. Trying pyttsx3 fallback.")
    GTTS_AVAILABLE = False

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    logger.warning("pyttsx3 not installed. TTS output will be text-only.")
    PYTTSX3_AVAILABLE = False

try:
    from playsound import playsound
    PLAYSOUND_AVAILABLE = True
except ImportError:
    PLAYSOUND_AVAILABLE = False

AUDIO_DIR = os.path.join(os.path.dirname(__file__), "audio")


# ──────────────────────────────────────────────
# TTS Result
# ──────────────────────────────────────────────

class TTSResult:
    def __init__(
        self,
        text: str,
        audio_path: Optional[str] = None,
        engine: str = "none",
        duration_s: float = 0.0,
        error: str = "",
    ):
        self.text       = text
        self.audio_path = audio_path
        self.engine     = engine
        self.duration_s = duration_s
        self.error      = error
        self.success    = audio_path is not None or (not error and engine != "none")
        self.timestamp  = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "text"      : self.text,
            "audio_path": self.audio_path,
            "engine"    : self.engine,
            "duration_s": self.duration_s,
            "error"     : self.error,
            "success"   : self.success,
            "timestamp" : self.timestamp,
        }


# ──────────────────────────────────────────────
# Text to Speech
# ──────────────────────────────────────────────

class TextToSpeech:
    """
    Converts text to speech audio using gTTS (online) or pyttsx3 (offline).
    """

    # Language codes supported by gTTS
    SUPPORTED_LANGUAGES = {
        "en": "English",
        "hi": "Hindi",
        "te": "Telugu",
        "ta": "Tamil",
        "kn": "Kannada",
        "mr": "Marathi",
        "gu": "Gujarati",
        "bn": "Bengali",
    }

    def __init__(
        self,
        language: str = "en",
        slow: bool = False,
        save_audio: bool = True,
        autoplay: bool = False,
    ):
        """
        Args:
            language  : Language code (e.g., "en", "hi")
            slow      : If True, speak slowly (gTTS only)
            save_audio: If True, save generated audio files
            autoplay  : If True, play audio immediately after generation
        """
        self.language   = language
        self.slow       = slow
        self.save_audio = save_audio
        self.autoplay   = autoplay
        self._pyttsx3_engine = None

        if not GTTS_AVAILABLE and PYTTSX3_AVAILABLE:
            self._pyttsx3_engine = self._init_pyttsx3()

        if save_audio:
            os.makedirs(AUDIO_DIR, exist_ok=True)

    def _init_pyttsx3(self):
        """Initialize pyttsx3 engine."""
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", 160)    # Words per minute
            engine.setProperty("volume", 0.9)
            voices = engine.getProperty("voices")
            # Prefer female voice if available
            for v in voices:
                if "female" in v.name.lower() or "zira" in v.name.lower():
                    engine.setProperty("voice", v.id)
                    break
            return engine
        except Exception as e:
            logger.warning(f"pyttsx3 init failed: {e}")
            return None

    # ── Public Interface ──────────────────────────────────────────────────

    def speak(self, text: str, language: Optional[str] = None) -> TTSResult:
        """
        Convert text to speech. If autoplay=True, play immediately.

        Args:
            text    : Text string to convert.
            language: Override default language for this call.

        Returns:
            TTSResult
        """
        lang = language or self.language
        text = text.strip()

        if not text:
            return TTSResult("", error="Empty text provided.")

        # Try gTTS first
        if GTTS_AVAILABLE:
            result = self._gtts_speak(text, lang)
        elif self._pyttsx3_engine:
            result = self._pyttsx3_speak(text)
        else:
            logger.warning(f"[TTS TEXT-ONLY] {text}")
            return TTSResult(text, engine="text_only")

        if result.success and self.autoplay and result.audio_path:
            self._play_audio(result.audio_path)

        return result

    def speak_async(self, text: str, language: Optional[str] = None):
        """Speak in a background thread without blocking."""
        import threading
        t = threading.Thread(target=self.speak, args=(text, language), daemon=True)
        t.start()

    def save_to_file(self, text: str, output_path: str, language: Optional[str] = None) -> str:
        """
        Convert text to speech and save to a specific file path.

        Returns:
            Output file path.
        """
        lang = language or self.language
        if GTTS_AVAILABLE:
            tts = gTTS(text=text, lang=lang, slow=self.slow)
            tts.save(output_path)
            return output_path
        raise RuntimeError("No TTS engine available.")

    def get_audio_bytes(self, text: str, language: Optional[str] = None) -> Optional[bytes]:
        """
        Convert text to audio and return raw bytes (for streaming/API).

        Returns:
            MP3 bytes or None on failure.
        """
        lang = language or self.language
        if not GTTS_AVAILABLE:
            return None
        try:
            buf = io.BytesIO()
            tts = gTTS(text=text, lang=lang, slow=self.slow)
            tts.write_to_fp(buf)
            return buf.getvalue()
        except Exception as e:
            logger.error(f"gTTS bytes error: {e}")
            return None

    # ── Parking-Specific Announcements ────────────────────────────────────

    def announce_slot_found(self, slot_id: str, zone: str = "") -> TTSResult:
        msg = f"Slot {slot_id} is available."
        if zone:
            msg += f" Please proceed to Zone {zone}."
        return self.speak(msg)

    def announce_slot_taken(self, slot_id: str) -> TTSResult:
        return self.speak(f"Sorry, slot {slot_id} has just been taken. Finding you another slot.")

    def announce_session_end(self, amount: float) -> TTSResult:
        return self.speak(
            f"Your parking session has ended. Total amount: Rupees {amount:.0f}. "
            f"Thank you for using ParkPilot. Have a safe journey!"
        )

    def announce_ev_ready(self, charger_id: str) -> TTSResult:
        return self.speak(f"EV Charger {charger_id} is now available. Please move your vehicle.")

    def announce_lot_full(self) -> TTSResult:
        return self.speak("The parking lot is currently full. Please wait or try an alternate lot.")

    def announce_price(self, rate: float, demand_level: str = "") -> TTSResult:
        surge_text = ""
        if demand_level == "very_high":
            surge_text = " Surge pricing is currently active."
        elif demand_level == "high":
            surge_text = " Parking demand is high."
        return self.speak(f"Current parking rate is Rupees {rate:.0f} per hour.{surge_text}")

    # ── Engines ───────────────────────────────────────────────────────────

    def _gtts_speak(self, text: str, language: str) -> TTSResult:
        """Generate speech using Google TTS."""
        import time
        start = time.time()
        try:
            tts_obj = gTTS(text=text, lang=language, slow=self.slow)

            if self.save_audio:
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                out_path = os.path.join(AUDIO_DIR, f"tts_{ts}.mp3")
                tts_obj.save(out_path)
                elapsed = time.time() - start
                return TTSResult(text, audio_path=out_path, engine="gtts",
                                 duration_s=round(elapsed, 2))
            else:
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                    tts_obj.save(tmp.name)
                    elapsed = time.time() - start
                    return TTSResult(text, audio_path=tmp.name, engine="gtts",
                                     duration_s=round(elapsed, 2))
        except Exception as e:
            logger.error(f"gTTS error: {e}")
            return TTSResult(text, error=str(e), engine="gtts")

    def _pyttsx3_speak(self, text: str) -> TTSResult:
        """Generate speech using pyttsx3 (offline)."""
        import time
        start = time.time()
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_path = os.path.join(AUDIO_DIR, f"tts_{ts}.wav") if self.save_audio else None

            if out_path:
                self._pyttsx3_engine.save_to_file(text, out_path)
                self._pyttsx3_engine.runAndWait()
            else:
                self._pyttsx3_engine.say(text)
                self._pyttsx3_engine.runAndWait()

            elapsed = time.time() - start
            return TTSResult(text, audio_path=out_path, engine="pyttsx3",
                             duration_s=round(elapsed, 2))
        except Exception as e:
            logger.error(f"pyttsx3 error: {e}")
            return TTSResult(text, error=str(e), engine="pyttsx3")

    def _play_audio(self, path: str):
        """Play audio file if playsound is available."""
        if PLAYSOUND_AVAILABLE:
            try:
                playsound(path)
            except Exception as e:
                logger.warning(f"Playback error: {e}")
        else:
            logger.info(f"Audio saved (install playsound to auto-play): {path}")


# ──────────────────────────────────────────────
# CLI Demo
# ──────────────────────────────────────────────

if __name__ == "__main__":
    tts = TextToSpeech(language="en", save_audio=True, autoplay=False)

    announcements = [
        "Welcome to ParkPilot. Your intelligent parking assistant.",
        "Slot A3 is available. Please proceed to Zone A.",
        "Your parking session has ended. Total amount: Rupees 60. Have a safe journey!",
        "Warning: EV charger is available. Please move your vehicle to charging bay.",
    ]

    print("=== TTS Demo ===")
    for text in announcements:
        result = tts.speak(text)
        print(f"  ✓ '{text[:50]}…'  →  {result.engine} | {result.audio_path or 'no file'}")
