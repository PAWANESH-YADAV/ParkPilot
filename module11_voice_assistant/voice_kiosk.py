"""
Module 11 — Voice Kiosk Integration
=======================================
Full kiosk integration that ties together STT → Intent Detection
→ Business Logic → TTS response in a continuous voice interaction loop.

This is the main entry point for the parking lot voice assistant kiosk.

Usage:
    from module11_voice_assistant.voice_kiosk import VoiceKiosk
    kiosk = VoiceKiosk(lot_id=1)
    kiosk.run()   # Starts interactive loop
"""

import os
import json
import logging
import threading
import time
from datetime import datetime
from typing import Optional, Callable

logger = logging.getLogger(__name__)

from module11_voice_assistant.speech_to_text import SpeechToText, WHISPER_AVAILABLE, SR_AVAILABLE
from module11_voice_assistant.intent_detector import IntentDetector, IntentResult
from module11_voice_assistant.text_to_speech import TextToSpeech, GTTS_AVAILABLE, PYTTSX3_AVAILABLE

KIOSK_LOG_DIR = os.path.join(os.path.dirname(__file__), "kiosk_logs")


# ──────────────────────────────────────────────
# Session State
# ──────────────────────────────────────────────

class KioskSession:
    """Tracks state for a single user interaction with the kiosk."""

    def __init__(self, session_id: str, lot_id: int):
        self.session_id = session_id
        self.lot_id     = lot_id
        self.started_at = datetime.now()
        self.ended_at: Optional[datetime] = None
        self.commands: list[dict] = []
        self.slot_id: Optional[str] = None
        self.plate_number: Optional[str] = None
        self.awaiting_confirmation: Optional[str] = None  # intent waiting for yes/no

    @property
    def duration_s(self) -> float:
        end = self.ended_at or datetime.now()
        return (end - self.started_at).total_seconds()

    def log_command(self, intent: IntentResult, response: str):
        self.commands.append({
            "timestamp" : datetime.now().isoformat(),
            "raw_text"  : intent.raw_text,
            "intent"    : intent.intent,
            "confidence": intent.confidence,
            "entities"  : intent.entities,
            "response"  : response,
        })

    def to_dict(self) -> dict:
        return {
            "session_id"   : self.session_id,
            "lot_id"       : self.lot_id,
            "started_at"   : self.started_at.isoformat(),
            "ended_at"     : self.ended_at.isoformat() if self.ended_at else None,
            "duration_s"   : round(self.duration_s, 2),
            "commands"     : self.commands,
            "slot_assigned": self.slot_id,
            "plate_number" : self.plate_number,
        }


# ──────────────────────────────────────────────
# Voice Kiosk
# ──────────────────────────────────────────────

class VoiceKiosk:
    """
    Full end-to-end voice assistant for a ParkPilot kiosk.

    Pipeline:
        Microphone → STT → Intent Detector → Business Handler → TTS → Speaker

    Business handlers (slot lookup, reservation, pricing) connect to
    the backend API. Provide a `api_client` to make real calls;
    otherwise realistic stub responses are used.
    """

    WAKE_WORDS = ["park pilot", "parkpilot", "hey pilot", "hello pilot", "parking"]

    def __init__(
        self,
        lot_id: int = 1,
        language: str = "en",
        stt_model: str = "base",
        api_client: Optional[object] = None,
        on_command_logged: Optional[Callable[[dict], None]] = None,
    ):
        self.lot_id     = lot_id
        self.language   = language
        self.api_client = api_client
        self._on_command_logged = on_command_logged

        self.stt      = SpeechToText(model=stt_model, language=language)
        self.detector = IntentDetector()
        self.tts      = TextToSpeech(language=language, save_audio=True, autoplay=True)

        self._running        = False
        self._current_session: Optional[KioskSession] = None
        self._session_history: list[KioskSession] = []
        self._session_counter = 0

        os.makedirs(KIOSK_LOG_DIR, exist_ok=True)

    # ── Main Loop ─────────────────────────────────────────────────────────

    def run(self, use_microphone: bool = True, test_commands: Optional[list[str]] = None):
        """
        Start the voice kiosk.

        Args:
            use_microphone: If True, listen from mic; if False use test_commands.
            test_commands : List of text commands to process (for testing).
        """
        self._running = True
        self._greet()

        if not use_microphone and test_commands:
            for cmd_text in test_commands:
                if not self._running:
                    break
                logger.info(f"[TEST INPUT] {cmd_text}")
                self._process_text_input(cmd_text)
            self._farewell()
            return

        # Real microphone mode
        if not (WHISPER_AVAILABLE or SR_AVAILABLE):
            logger.error("No STT engine available. Cannot run voice kiosk.")
            print("ERROR: Install 'openai-whisper' or 'SpeechRecognition' to use the voice kiosk.")
            return

        logger.info("Voice Kiosk running. Say a parking command to begin.")
        self.stt.listen_continuous(
            on_result=lambda r: self._process_text_input(r.text),
            phrase_time_limit=8.0,
            stop_phrase="goodbye",
        )

        self._farewell()

    def stop(self):
        """Stop the kiosk loop."""
        self._running = False

    # ── Text Processing ───────────────────────────────────────────────────

    def _process_text_input(self, text: str):
        """
        Process a single voice command text through the full pipeline.
        """
        if not text or not self._running:
            return

        logger.info(f"Processing: '{text}'")

        # Start session if none active
        if not self._current_session:
            self._start_session()

        # Detect intent
        intent_result = self.detector.detect(text)
        logger.info(f"Intent: {intent_result.intent} ({intent_result.confidence:.2f})")

        # Handle confirmation flow
        if self._current_session.awaiting_confirmation:
            response = self._handle_confirmation(intent_result)
        else:
            response = self._dispatch_intent(intent_result)

        # Respond
        self.tts.speak(response)
        self._current_session.log_command(intent_result, response)

        if self._on_command_logged:
            self._on_command_logged(self._current_session.commands[-1])

        # End session on exit intent
        if intent_result.intent == "end_session":
            self._end_session()

    # ── Intent Dispatch ───────────────────────────────────────────────────

    def _dispatch_intent(self, intent: IntentResult) -> str:
        """Route intent to the appropriate handler and return response text."""
        handlers = {
            "find_slot"         : self._handle_find_slot,
            "reserve_slot"      : self._handle_reserve_slot,
            "check_availability": self._handle_check_availability,
            "get_directions"    : self._handle_get_directions,
            "check_ev_charger"  : self._handle_check_ev_charger,
            "get_price"         : self._handle_get_price,
            "end_session"       : self._handle_end_session,
            "help"              : self._handle_help,
            "cancel"            : self._handle_cancel,
            "unknown"           : self._handle_unknown,
        }
        handler = handlers.get(intent.intent, self._handle_unknown)
        return handler(intent)

    # ── Business Handlers ─────────────────────────────────────────────────

    def _handle_find_slot(self, intent: IntentResult) -> str:
        """Find the nearest available slot."""
        vtype = intent.entities.get("vehicle_type", "car")
        zone  = intent.entities.get("zone", "")

        if self.api_client:
            try:
                slots = self.api_client.get_available_slots(lot_id=self.lot_id, vehicle_type=vtype)
                if slots:
                    slot = slots[0]
                    self._current_session.slot_id = slot["slot_number"]
                    return (
                        f"I found an available slot for your {vtype}. "
                        f"Slot {slot['slot_number']} in Zone {slot.get('zone', 'A')}. "
                        f"Please proceed there now."
                    )
                return "No slots are available right now. Please wait a moment."
            except Exception:
                pass

        # Stub response
        import random
        slot_id = f"A{random.randint(1, 8)}"
        self._current_session.slot_id = slot_id
        zone_text = f" in Zone {zone}" if zone else " in Zone A"
        return (
            f"I found slot {slot_id}{zone_text} available for your {vtype}. "
            f"Follow the green LED arrows to reach it."
        )

    def _handle_reserve_slot(self, intent: IntentResult) -> str:
        slot_id = intent.entities.get("slot_id") or self._current_session.slot_id
        hours   = intent.entities.get("duration_hours", 2.0)
        if not slot_id:
            return "Which slot would you like to reserve? Please say the slot number."
        self._current_session.awaiting_confirmation = "reserve_slot"
        self._current_session.slot_id = slot_id
        return (
            f"I'll reserve slot {slot_id} for {hours:.0f} hour(s). "
            f"Shall I confirm this reservation? Say yes or no."
        )

    def _handle_check_availability(self, intent: IntentResult) -> str:
        if self.api_client:
            try:
                data = self.api_client.get_lot_status(self.lot_id)
                avail = data.get("available_slots", 0)
                total = data.get("total_slots", 0)
                return (
                    f"Currently, {avail} out of {total} slots are available. "
                    f"Occupancy is at {int((total-avail)/max(1,total)*100)} percent."
                )
            except Exception:
                pass
        import random
        avail = random.randint(10, 45)
        return (
            f"Currently {avail} parking slots are available across all zones. "
            f"Zone A has the most availability."
        )

    def _handle_get_directions(self, intent: IntentResult) -> str:
        slot_id = intent.entities.get("slot_id") or self._current_session.slot_id
        if slot_id:
            return (
                f"Directing you to slot {slot_id}. "
                f"Follow the blue LED arrows on the floor. "
                f"Turn left at the elevator and continue straight."
            )
        return "Where would you like to go? The exit, elevator, or a specific slot?"

    def _handle_check_ev_charger(self, intent: IntentResult) -> str:
        import random
        available = random.randint(0, 3)
        if available > 0:
            return (
                f"{available} EV charging bay(s) are available on Level 2. "
                f"Slots C1 through C3 are EV dedicated. "
                f"Charging rate is ₹8 per kWh."
            )
        return "All EV charging bays are currently occupied. We'll notify you when one becomes free."

    def _handle_get_price(self, intent: IntentResult) -> str:
        import random
        rate = random.choice([30, 35, 40, 45, 50])
        return (
            f"The current parking rate is ₹{rate} per hour. "
            f"EV vehicles get a 10% discount. "
            f"Rates may vary with demand."
        )

    def _handle_end_session(self, intent: IntentResult) -> str:
        if self._current_session and self._current_session.commands:
            duration = self._current_session.duration_s / 3600
            amount = round(30 * duration, 2)
            return (
                f"Ending your session. "
                f"Duration: {duration:.1f} hours. "
                f"Total: ₹{amount:.0f}. "
                f"Thank you for using ParkPilot!"
            )
        return "Goodbye! Thank you for using ParkPilot. Have a safe journey!"

    def _handle_help(self, intent: IntentResult) -> str:
        return (
            "I can help you with: finding a parking slot, reserving a slot, "
            "checking availability, getting directions, EV charger status, "
            "current parking rates, or ending your session. "
            "Just tell me what you need!"
        )

    def _handle_cancel(self, intent: IntentResult) -> str:
        self._current_session.awaiting_confirmation = None
        return "Cancellation confirmed. Is there anything else I can help you with?"

    def _handle_unknown(self, intent: IntentResult) -> str:
        return (
            "I'm sorry, I didn't quite catch that. "
            "You can say things like: find slot, check availability, "
            "get directions, or help."
        )

    def _handle_confirmation(self, intent: IntentResult) -> str:
        """Handle yes/no confirmation for pending intents."""
        pending = self._current_session.awaiting_confirmation
        confirmed = intent.entities.get("confirmation")
        self._current_session.awaiting_confirmation = None

        if confirmed is True or intent.intent == "reserve_slot":
            if pending == "reserve_slot":
                slot_id = self._current_session.slot_id
                return (
                    f"Slot {slot_id} has been reserved. "
                    f"A QR code has been sent to your mobile. "
                    f"Please arrive within 15 minutes."
                )
        return "Reservation cancelled. Let me know if you need anything else."

    # ── Session Management ────────────────────────────────────────────────

    def _start_session(self):
        self._session_counter += 1
        sid = f"KIOSK-{self.lot_id}-{self._session_counter:04d}"
        self._current_session = KioskSession(sid, self.lot_id)
        logger.info(f"Kiosk session started: {sid}")

    def _end_session(self):
        if self._current_session:
            self._current_session.ended_at = datetime.now()
            self._session_history.append(self._current_session)
            self._save_session_log(self._current_session)
            logger.info(f"Session ended: {self._current_session.session_id}")
            self._current_session = None

    def _save_session_log(self, session: KioskSession):
        filename = f"{session.session_id}.json"
        filepath = os.path.join(KIOSK_LOG_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(session.to_dict(), f, indent=2)

    # ── Announcements ─────────────────────────────────────────────────────

    def _greet(self):
        msg = "Welcome to ParkPilot. Your intelligent parking assistant. How can I help you today?"
        logger.info(f"[KIOSK GREETING] {msg}")
        self.tts.speak(msg)

    def _farewell(self):
        msg = "ParkPilot kiosk session ended. Thank you for visiting."
        logger.info(f"[KIOSK FAREWELL] {msg}")
        self.tts.speak(msg)

    # ── Stats ─────────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        return {
            "total_sessions"  : len(self._session_history),
            "total_commands"  : sum(len(s.commands) for s in self._session_history),
            "avg_session_s"   : round(
                sum(s.duration_s for s in self._session_history) /
                max(1, len(self._session_history)), 2
            ),
            "lot_id"          : self.lot_id,
        }


# ──────────────────────────────────────────────
# CLI Demo
# ──────────────────────────────────────────────

if __name__ == "__main__":
    kiosk = VoiceKiosk(lot_id=1, language="en")

    test_commands = [
        "Find me a free parking slot",
        "Reserve slot A5 for 2 hours",
        "yes",
        "Is there an EV charger available?",
        "What is the current parking price?",
        "Take me to the elevator",
        "I'm done parking, goodbye",
    ]

    print("=== ParkPilot Voice Kiosk — Text Demo ===\n")
    kiosk.run(use_microphone=False, test_commands=test_commands)

    print("\n=== Kiosk Stats ===")
    stats = kiosk.get_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")
