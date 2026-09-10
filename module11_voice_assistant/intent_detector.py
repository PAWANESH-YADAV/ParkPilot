"""
Module 11 — Intent Detector
==============================
NLP-based intent classifier for ParkPilot voice commands.
Uses keyword matching with pattern scoring, with optional
Hugging Face / spaCy upgrades when installed.

Supported intents:
    find_slot, reserve_slot, check_availability, get_directions,
    check_ev_charger, get_price, end_session, help, cancel, unknown

Usage:
    from module11_voice_assistant.intent_detector import IntentDetector
    detector = IntentDetector()
    result = detector.detect("Is there a free parking space near the elevator?")
"""

import re
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
    logger.info("Transformers available for intent classification.")
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False


# ──────────────────────────────────────────────
# Intent Definitions
# ──────────────────────────────────────────────

INTENT_PATTERNS: dict[str, list[str]] = {
    "find_slot": [
        r"\b(find|show|give|get|where|available|empty|free|open)\b.*(slot|space|parking|spot)",
        r"(slot|space|parking).*(available|free|empty|open)",
        r"park\s*(my\s*car|vehicle|here|now)",
        r"(any|which).*(slot|space|spot).*(free|open|empty)",
    ],
    "reserve_slot": [
        r"\b(book|reserve|pre.?book|hold|block)\b.*(slot|space|parking|spot)",
        r"(slot|space|parking).*(book|reserve|hold)",
        r"(I want|can you|please).*(book|reserve)",
    ],
    "check_availability": [
        r"\b(how many|count|total|number of).*(slot|space|parking|spot)",
        r"(occupancy|availability|capacity|status)",
        r"(is.*(full|available)|parking.*(status|count))",
    ],
    "get_directions": [
        r"\b(direction|navigate|guide|lead|take|how do I get|where is)\b",
        r"(show|find).*(way|route|path|map)",
        r"(go to|reach|find).*(slot|exit|elevator|staircase|reception)",
    ],
    "check_ev_charger": [
        r"\b(ev|electric|charge|charger|charging)\b",
        r"(charge|charging).*(station|point|bay|slot)",
        r"(available|free|open).*(ev|electric|charger)",
    ],
    "get_price": [
        r"\b(price|rate|cost|fee|charge|how much|tariff)\b",
        r"(parking|hourly).*(rate|price|cost)",
        r"(what does|how much).*(cost|charge|rate)",
    ],
    "end_session": [
        r"\b(exit|leave|done|finish|checkout|check.out|I am done|leaving)\b",
        r"(end|close|stop|terminate).*(session|parking)",
        r"(I.*(am|'m|will).*(going|leaving|done))",
    ],
    "help": [
        r"\b(help|assist|support|what can you|commands|options)\b",
        r"(I need|give me).*(help|assistance)",
        r"\b(how to|how do)\b",
    ],
    "cancel": [
        r"\b(cancel|abort|undo|never mind|stop|dismiss)\b",
        r"(cancel|undo).*(book|reserv|session)",
    ],
}

# Slot number extraction patterns
SLOT_PATTERN   = r"\b([A-Ca-c]\d{1,2}|slot\s*[A-Ca-c]?\d{1,2})\b"
VEHICLE_PATTERN = r"\b(car|bike|ev|truck|handicap|electric)\b"
DURATION_PATTERN = r"\b(\d+)\s*(hour|hr|minute|min|day)\b"


# ──────────────────────────────────────────────
# Intent Result
# ──────────────────────────────────────────────

class IntentResult:
    def __init__(
        self,
        intent: str,
        confidence: float,
        entities: Optional[dict] = None,
        raw_text: str = "",
        engine: str = "keyword",
    ):
        self.intent     = intent
        self.confidence = confidence
        self.entities   = entities or {}
        self.raw_text   = raw_text
        self.engine     = engine
        self.timestamp  = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "intent"    : self.intent,
            "confidence": round(self.confidence, 4),
            "entities"  : self.entities,
            "raw_text"  : self.raw_text,
            "engine"    : self.engine,
            "timestamp" : self.timestamp,
        }

    def __repr__(self):
        return f'IntentResult(intent={self.intent}, conf={self.confidence:.2f}, ent={self.entities})'


# ──────────────────────────────────────────────
# Intent Detector
# ──────────────────────────────────────────────

class IntentDetector:
    """
    Classifies user intent from natural language voice commands.
    Uses compiled regex patterns for fast keyword matching.
    """

    def __init__(self, use_transformers: bool = False, model_name: str = "zero-shot-classification"):
        self._compiled: dict[str, list] = {
            intent: [re.compile(p, re.IGNORECASE) for p in patterns]
            for intent, patterns in INTENT_PATTERNS.items()
        }
        self._transformer_pipe = None

        if use_transformers and TRANSFORMERS_AVAILABLE:
            try:
                self._transformer_pipe = pipeline(
                    "zero-shot-classification",
                    model="facebook/bart-large-mnli"
                )
                logger.info("Transformer zero-shot classifier loaded.")
            except Exception as e:
                logger.warning(f"Could not load transformer: {e}")

    # ── Public ────────────────────────────────────────────────────────────

    def detect(self, text: str) -> IntentResult:
        """
        Detect the intent from a natural language string.

        Args:
            text: Transcribed voice command text.

        Returns:
            IntentResult with intent, confidence, and extracted entities.
        """
        text = text.strip()
        if not text:
            return IntentResult("unknown", 0.0, raw_text=text)

        # Try transformer first if available
        if self._transformer_pipe:
            return self._transformer_detect(text)

        return self._keyword_detect(text)

    def detect_batch(self, texts: list[str]) -> list[IntentResult]:
        return [self.detect(t) for t in texts]

    # ── Keyword Detection ─────────────────────────────────────────────────

    def _keyword_detect(self, text: str) -> IntentResult:
        """Score each intent using compiled regex patterns."""
        scores: dict[str, float] = {}

        for intent, patterns in self._compiled.items():
            matched = sum(1 for p in patterns if p.search(text))
            if matched > 0:
                scores[intent] = matched / len(patterns)

        if not scores:
            return IntentResult("unknown", 0.0, raw_text=text, engine="keyword")

        best_intent  = max(scores, key=scores.get)
        confidence   = min(1.0, scores[best_intent] * 1.5)  # Scale up
        entities     = self._extract_entities(text, best_intent)

        logger.debug(f"Intent: {best_intent} ({confidence:.2f}) | scores={scores}")
        return IntentResult(
            intent=best_intent,
            confidence=round(confidence, 4),
            entities=entities,
            raw_text=text,
            engine="keyword",
        )

    # ── Transformer Detection ─────────────────────────────────────────────

    def _transformer_detect(self, text: str) -> IntentResult:
        """Zero-shot classification using HuggingFace Transformers."""
        candidate_labels = list(INTENT_PATTERNS.keys())
        try:
            output = self._transformer_pipe(text, candidate_labels)
            best_label = output["labels"][0]
            score = output["scores"][0]
            entities = self._extract_entities(text, best_label)
            return IntentResult(
                intent=best_label,
                confidence=round(score, 4),
                entities=entities,
                raw_text=text,
                engine="transformer",
            )
        except Exception as e:
            logger.warning(f"Transformer inference failed: {e}. Falling back to keyword.")
            return self._keyword_detect(text)

    # ── Entity Extraction ─────────────────────────────────────────────────

    def _extract_entities(self, text: str, intent: str) -> dict:
        """Extract named entities relevant to the detected intent."""
        entities: dict = {}

        # Slot number (e.g., "A3", "slot B7")
        slot_match = re.search(SLOT_PATTERN, text, re.IGNORECASE)
        if slot_match:
            raw = slot_match.group(1).replace("slot", "").strip().upper()
            entities["slot_id"] = raw

        # Vehicle type
        vehicle_match = re.search(VEHICLE_PATTERN, text, re.IGNORECASE)
        if vehicle_match:
            vt = vehicle_match.group(1).lower()
            entities["vehicle_type"] = "ev" if vt == "electric" else vt

        # Duration
        duration_match = re.search(DURATION_PATTERN, text, re.IGNORECASE)
        if duration_match:
            amount = int(duration_match.group(1))
            unit   = duration_match.group(2).lower()
            # Normalise to hours
            hours = amount if "hour" in unit or "hr" in unit else amount / 60
            entities["duration_hours"] = round(hours, 2)

        # Zone (A, B, C)
        zone_match = re.search(r"\bzone\s*([ABC])\b", text, re.IGNORECASE)
        if zone_match:
            entities["zone"] = zone_match.group(1).upper()

        # Yes/No
        if re.search(r"\b(yes|yeah|ok|okay|sure|correct|confirm)\b", text, re.IGNORECASE):
            entities["confirmation"] = True
        if re.search(r"\b(no|nope|cancel|never mind)\b", text, re.IGNORECASE):
            entities["confirmation"] = False

        return entities

    # ── Response Templates ────────────────────────────────────────────────

    def get_response_template(self, intent: str, entities: dict) -> str:
        """Return a natural language response template for a given intent."""
        slot = entities.get("slot_id", "")
        templates = {
            "find_slot"          : f"I'll find you the nearest available parking slot.",
            "reserve_slot"       : f"{'Reserving slot ' + slot if slot else 'Please confirm which slot to reserve.'}",
            "check_availability" : "Let me check the current parking availability.",
            "get_directions"     : f"{'Showing directions to slot ' + slot + '.' if slot else 'Where would you like to go?'}",
            "check_ev_charger"   : "Checking EV charger availability right now.",
            "get_price"          : "The current parking rate is displayed on screen.",
            "end_session"        : "Ending your parking session. Thank you for using ParkPilot!",
            "help"               : "You can say: find slot, reserve slot, check availability, get directions, or check EV charger.",
            "cancel"             : "Cancellation confirmed.",
            "unknown"            : "I didn't understand that. Please try again or say 'help'.",
        }
        return templates.get(intent, "I'm processing your request.")


# ──────────────────────────────────────────────
# CLI Demo
# ──────────────────────────────────────────────

if __name__ == "__main__":
    detector = IntentDetector()

    test_commands = [
        "Find me a free parking slot near zone A",
        "Reserve slot B7 for 2 hours",
        "How many slots are available?",
        "Take me to the elevator",
        "Is there an EV charger free?",
        "What is the current parking price?",
        "I'm done parking, I'm leaving now",
        "Can you help me?",
        "Cancel my reservation",
        "Bla bla random gibberish 123",
    ]

    print("=== Intent Detection Results ===\n")
    print(f"{'Command':45s} {'Intent':22s} {'Conf':6s} {'Entities'}")
    print("─" * 100)
    for cmd in test_commands:
        result = detector.detect(cmd)
        ent_str = str(result.entities) if result.entities else "—"
        print(
            f"{cmd[:44]:45s} {result.intent:22s} "
            f"{result.confidence:.2f}  {ent_str}"
        )
