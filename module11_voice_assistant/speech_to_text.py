"""
Module 11 — Speech-to-Text (STT)
==================================
Converts spoken audio to text using OpenAI's Whisper model.
Falls back to Google Speech Recognition when Whisper is unavailable.

Dependencies (optional):
    pip install openai-whisper SpeechRecognition sounddevice

Usage:
    from module11_voice_assistant.speech_to_text import SpeechToText
    stt = SpeechToText(model="base")
    result = stt.transcribe_file("audio/command.wav")
    # OR
    result = stt.transcribe_microphone(duration=5)
"""

import os
import io
import logging
import tempfile
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# ── Whisper ───────────────────────────────────────────────────────────────────
try:
    import whisper
    import numpy as np
    WHISPER_AVAILABLE = True
    logger.info("OpenAI Whisper loaded.")
except ImportError:
    logger.warning("openai-whisper not installed. Trying SpeechRecognition fallback.")
    WHISPER_AVAILABLE = False

# ── SpeechRecognition fallback ────────────────────────────────────────────────
try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    logger.warning("SpeechRecognition not installed.")
    SR_AVAILABLE = False

# ── Audio recording ───────────────────────────────────────────────────────────
try:
    import sounddevice as sd
    import soundfile as sf
    AUDIO_AVAILABLE = True
except ImportError:
    logger.warning("sounddevice/soundfile not installed. Microphone recording disabled.")
    AUDIO_AVAILABLE = False


# ──────────────────────────────────────────────
# STT Result
# ──────────────────────────────────────────────

class STTResult:
    def __init__(
        self,
        text: str,
        language: str = "en",
        confidence: float = 1.0,
        duration_s: float = 0.0,
        engine: str = "unknown",
        error: str = "",
    ):
        self.text       = text.strip()
        self.language   = language
        self.confidence = confidence
        self.duration_s = duration_s
        self.engine     = engine
        self.error      = error
        self.timestamp  = datetime.now().isoformat()
        self.success    = bool(text) and not error

    def to_dict(self) -> dict:
        return {
            "text"      : self.text,
            "language"  : self.language,
            "confidence": self.confidence,
            "duration_s": self.duration_s,
            "engine"    : self.engine,
            "error"     : self.error,
            "success"   : self.success,
            "timestamp" : self.timestamp,
        }

    def __repr__(self):
        return f'STTResult(text="{self.text[:40]}…", engine={self.engine}, ok={self.success})'


# ──────────────────────────────────────────────
# Speech to Text
# ──────────────────────────────────────────────

class SpeechToText:
    """
    Transcribes audio using Whisper (primary) or Google STT (fallback).
    """

    SUPPORTED_MODELS = ["tiny", "base", "small", "medium", "large"]

    def __init__(self, model: str = "base", language: str = "en"):
        """
        Args:
            model   : Whisper model size ("tiny", "base", "small", "medium", "large")
            language: ISO language code ("en", "hi", "te", etc.)
        """
        self.language = language
        self._whisper_model = None
        self._sr_recognizer = None

        if WHISPER_AVAILABLE:
            try:
                logger.info(f"Loading Whisper model: {model}")
                self._whisper_model = whisper.load_model(model)
                logger.info("Whisper model ready.")
            except Exception as e:
                logger.warning(f"Could not load Whisper: {e}")

        if SR_AVAILABLE:
            self._sr_recognizer = sr.Recognizer()
            self._sr_recognizer.energy_threshold = 300
            self._sr_recognizer.dynamic_energy_threshold = True

    # ── File Transcription ────────────────────────────────────────────────

    def transcribe_file(self, audio_path: str) -> STTResult:
        """
        Transcribe a WAV/MP3/FLAC audio file.

        Args:
            audio_path: Path to the audio file.

        Returns:
            STTResult
        """
        if not os.path.exists(audio_path):
            return STTResult("", error=f"File not found: {audio_path}")

        import time
        start = time.time()

        # Try Whisper first
        if self._whisper_model:
            return self._whisper_transcribe(audio_path, start)

        # Fall back to Google SR
        if self._sr_recognizer and SR_AVAILABLE:
            return self._sr_transcribe_file(audio_path, start)

        return STTResult("", error="No STT engine available. Install whisper or SpeechRecognition.")

    def _whisper_transcribe(self, audio_path: str, start: float) -> STTResult:
        """Run Whisper inference."""
        import time
        try:
            options = {
                "language"       : self.language if self.language != "auto" else None,
                "task"           : "transcribe",
                "fp16"           : False,
                "verbose"        : False,
            }
            result = self._whisper_model.transcribe(audio_path, **options)
            elapsed = time.time() - start

            detected_lang = result.get("language", self.language)
            text = result.get("text", "").strip()

            return STTResult(
                text=text,
                language=detected_lang,
                confidence=0.90,  # Whisper doesn't output raw confidence
                duration_s=round(elapsed, 2),
                engine="whisper",
            )
        except Exception as e:
            logger.error(f"Whisper transcription error: {e}")
            return STTResult("", error=str(e), engine="whisper")

    def _sr_transcribe_file(self, audio_path: str, start: float) -> STTResult:
        """Transcribe using Google Speech Recognition."""
        import time
        try:
            with sr.AudioFile(audio_path) as source:
                audio_data = self._sr_recognizer.record(source)
            text = self._sr_recognizer.recognize_google(audio_data, language=self.language)
            elapsed = time.time() - start
            return STTResult(
                text=text,
                language=self.language,
                confidence=0.75,
                duration_s=round(elapsed, 2),
                engine="google_sr",
            )
        except sr.UnknownValueError:
            return STTResult("", error="Could not understand audio.", engine="google_sr")
        except sr.RequestError as e:
            return STTResult("", error=f"Google STT API error: {e}", engine="google_sr")
        except Exception as e:
            return STTResult("", error=str(e), engine="google_sr")

    # ── Microphone Recording + Transcription ──────────────────────────────

    def transcribe_microphone(
        self,
        duration: float = 5.0,
        sample_rate: int = 16000,
    ) -> STTResult:
        """
        Record from microphone and transcribe.

        Args:
            duration   : Recording duration in seconds
            sample_rate: Audio sample rate (16 kHz for Whisper)

        Returns:
            STTResult
        """
        if not AUDIO_AVAILABLE:
            return STTResult("", error="sounddevice not installed. Cannot record microphone.")

        try:
            logger.info(f"Recording {duration}s from microphone…")
            audio = sd.rec(
                int(duration * sample_rate),
                samplerate=sample_rate,
                channels=1,
                dtype="float32",
            )
            sd.wait()

            # Save to temp WAV
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
            sf.write(tmp_path, audio, sample_rate)

            result = self.transcribe_file(tmp_path)
            os.unlink(tmp_path)
            return result

        except Exception as e:
            logger.error(f"Microphone recording error: {e}")
            return STTResult("", error=str(e))

    # ── Continuous Listening ──────────────────────────────────────────────

    def listen_continuous(
        self,
        on_result: callable,
        phrase_time_limit: float = 8.0,
        stop_phrase: str = "stop listening",
    ):
        """
        Listen continuously from microphone until stop phrase detected.

        Args:
            on_result       : Callback function receiving STTResult
            phrase_time_limit: Max seconds per utterance
            stop_phrase     : Phrase that stops listening loop
        """
        if not SR_AVAILABLE:
            logger.error("SpeechRecognition needed for continuous listening.")
            return

        logger.info("Continuous listening started. Say 'stop listening' to quit.")
        with sr.Microphone() as source:
            self._sr_recognizer.adjust_for_ambient_noise(source, duration=1.0)

            while True:
                try:
                    audio = self._sr_recognizer.listen(
                        source, phrase_time_limit=phrase_time_limit
                    )
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                        tmp.write(audio.get_wav_data())
                        tmp_path = tmp.name

                    result = self.transcribe_file(tmp_path)
                    os.unlink(tmp_path)

                    if result.success:
                        on_result(result)
                        if stop_phrase.lower() in result.text.lower():
                            logger.info("Stop phrase detected. Ending continuous listening.")
                            break
                except Exception as e:
                    logger.warning(f"Listen error: {e}")


# ──────────────────────────────────────────────
# CLI Demo
# ──────────────────────────────────────────────

if __name__ == "__main__":
    stt = SpeechToText(model="base")

    # Demo with a test file if available
    test_file = "test_audio.wav"
    if os.path.exists(test_file):
        result = stt.transcribe_file(test_file)
        print(f"Transcribed: {result.text}")
        print(f"Engine     : {result.engine}")
        print(f"Time       : {result.duration_s}s")
    else:
        print("No test audio file found.")
        print("Engine available:", "Whisper" if WHISPER_AVAILABLE else "Google SR" if SR_AVAILABLE else "None")
        print("To test: place a WAV file as 'test_audio.wav' and re-run.")
