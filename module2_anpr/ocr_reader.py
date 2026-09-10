"""
ParkPilot — Module 2: OCR Reader (EasyOCR)
Extracts the license plate number text from a cropped plate image.

Usage:
    from module2_anpr.ocr_reader import OCRReader
    reader = OCRReader()
    plate_text = reader.read_plate(plate_crop_image)
    print(plate_text)  # e.g. "KA05AB1234"
"""

import re
import cv2
import numpy as np
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import get_logger

logger = get_logger("parkpilot.module2.ocr")


class OCRReader:
    """
    License plate text extraction using EasyOCR.

    Applies preprocessing pipeline before OCR:
        1. Grayscale conversion
        2. CLAHE contrast enhancement
        3. Gaussian blur (denoise)
        4. Otsu thresholding
        5. Morphological cleanup
    Then runs EasyOCR and post-processes the result.

    Attributes:
        languages: OCR language list (default: ['en'])
        gpu: Use GPU acceleration if available
        confidence_threshold: Minimum OCR confidence to accept result
    """

    # Indian plate format patterns
    INDIAN_PLATE_PATTERNS = [
        r"^[A-Z]{2}\s?[0-9]{2}\s?[A-Z]{1,2}\s?[0-9]{4}$",   # KA05AB1234
        r"^[A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{4}$",               # KA05AB1234 (compact)
        r"^[0-9]{2}BH[0-9]{4}[A-Z]{2}$",                      # BH (Bharat) series
        r"^[A-Z]{2}[0-9]{2}[A-Z]{1}[0-9]{4}$",               # DL5C1234
    ]

    # Common OCR misread character fixes
    CHAR_FIXES = {
        "0": "O", "O": "0",  # Context-dependent (handled by position)
        "1": "I", "I": "1",
        "8": "B", "B": "8",
        "5": "S", "S": "5",
        "6": "G", "G": "6",
        "2": "Z", "Z": "2",
    }

    def __init__(
        self,
        languages: list = None,
        gpu: bool = False,
        confidence_threshold: float = 0.4
    ):
        self.languages = languages or ["en"]
        self.gpu = gpu
        self.confidence_threshold = confidence_threshold
        self._reader = None
        self._initialize_reader()

    def _initialize_reader(self):
        """Initialize EasyOCR reader (downloads model on first run)."""
        try:
            import easyocr
            self._reader = easyocr.Reader(
                self.languages,
                gpu=self.gpu,
                verbose=False
            )
            logger.info(f"EasyOCR initialized | Languages: {self.languages} | GPU: {self.gpu}")
        except ImportError:
            logger.warning("EasyOCR not installed. Using Tesseract fallback.")
            self._reader = None
        except Exception as e:
            logger.error(f"EasyOCR init failed: {e}")
            self._reader = None

    # ── Preprocessing ─────────────────────────────────────────────────────────

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess plate image for optimal OCR accuracy.

        Steps:
            1. Resize to standard size (400x100)
            2. Convert to grayscale
            3. CLAHE contrast enhancement
            4. Gaussian blur to reduce noise
            5. Otsu thresholding
            6. Morphological closing to fix broken characters

        Returns:
            Preprocessed binary image (grayscale)
        """
        if image is None or image.size == 0:
            return None

        # Resize to standard plate size
        img = cv2.resize(image, (400, 100))

        # Grayscale
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img.copy()

        # CLAHE — boost contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
        enhanced = clahe.apply(gray)

        # Gaussian blur
        blurred = cv2.GaussianBlur(enhanced, (3, 3), 0)

        # Otsu thresholding
        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Morphological closing — connect broken strokes
        kernel = np.ones((2, 2), np.uint8)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        return cleaned

    # ── OCR Extraction ────────────────────────────────────────────────────────

    def read_plate(self, plate_image: np.ndarray, raw: bool = False) -> dict:
        """
        Extract license plate text from a cropped plate image.

        Args:
            plate_image: Cropped plate image (BGR or grayscale)
            raw: If True, return raw OCR output without post-processing

        Returns:
            dict with keys:
                - text: Cleaned plate number (e.g. "KA05AB1234")
                - confidence: OCR confidence (0.0 to 1.0)
                - raw_text: Unprocessed OCR string
                - valid: Whether text matches known plate format
                - timestamp: ISO timestamp
        """
        result = {
            "text": "",
            "confidence": 0.0,
            "raw_text": "",
            "valid": False,
            "timestamp": datetime.utcnow().isoformat()
        }

        if plate_image is None or plate_image.size == 0:
            logger.warning("Empty plate image received")
            return result

        preprocessed = self.preprocess(plate_image)

        # Try EasyOCR first
        if self._reader is not None:
            easyocr_result = self._read_easyocr(preprocessed)
            if easyocr_result["confidence"] >= self.confidence_threshold:
                result.update(easyocr_result)
                if not raw:
                    result["text"] = self._post_process(result["raw_text"])
                result["valid"] = self._validate_plate(result["text"])
                return result

        # Fallback: Tesseract
        tesseract_result = self._read_tesseract(preprocessed)
        result.update(tesseract_result)
        if not raw:
            result["text"] = self._post_process(result["raw_text"])
        result["valid"] = self._validate_plate(result["text"])

        return result

    def _read_easyocr(self, image: np.ndarray) -> dict:
        """Run EasyOCR on preprocessed image."""
        try:
            results = self._reader.readtext(image, detail=1)
            if not results:
                return {"raw_text": "", "confidence": 0.0}

            # Take the highest-confidence result
            best = max(results, key=lambda x: x[2])
            _, text, conf = best

            return {"raw_text": text.strip(), "confidence": float(conf)}
        except Exception as e:
            logger.error(f"EasyOCR read error: {e}")
            return {"raw_text": "", "confidence": 0.0}

    def _read_tesseract(self, image: np.ndarray) -> dict:
        """Fallback OCR using pytesseract."""
        try:
            import pytesseract
            # Plate-specific config: assume single line, allow letters+digits
            config = "--oem 3 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            text = pytesseract.image_to_string(image, config=config).strip()
            return {"raw_text": text, "confidence": 0.6}
        except Exception as e:
            logger.warning(f"Tesseract fallback failed: {e}")
            return {"raw_text": "", "confidence": 0.0}

    # ── Post-Processing ───────────────────────────────────────────────────────

    def _post_process(self, raw_text: str) -> str:
        """
        Clean and normalize raw OCR text into a standard plate number.

        Steps:
            1. Uppercase + strip whitespace
            2. Remove non-alphanumeric characters
            3. Apply position-based character fixes
        """
        if not raw_text:
            return ""

        # Uppercase and remove spaces/special chars
        text = re.sub(r"[^A-Z0-9]", "", raw_text.upper().strip())

        if not text:
            return ""

        # Apply character correction based on position
        # Indian plates: first 2 = state code (letters), next 2 = district (digits),
        # then 1-2 letters + 4 digits
        chars = list(text)
        for i, ch in enumerate(chars):
            if i < 2:  # State code — must be letters
                if ch.isdigit() and ch in self.CHAR_FIXES:
                    chars[i] = self.CHAR_FIXES[ch]
            elif i < 4:  # District — must be digits
                if ch.isalpha() and ch in self.CHAR_FIXES:
                    chars[i] = self.CHAR_FIXES[ch]
            # Last 4 characters — must be digits
            elif i >= len(chars) - 4:
                if ch.isalpha() and ch in self.CHAR_FIXES:
                    chars[i] = self.CHAR_FIXES[ch]

        return "".join(chars)

    def _validate_plate(self, plate_text: str) -> bool:
        """Check if plate text matches a known Indian license plate format."""
        if not plate_text or len(plate_text) < 6:
            return False

        for pattern in self.INDIAN_PLATE_PATTERNS:
            if re.match(pattern, plate_text.replace(" ", "").upper()):
                return True

        return False

    # ── Batch Processing ──────────────────────────────────────────────────────

    def read_multiple(self, images: list) -> list:
        """
        Read plates from multiple images in sequence.

        Args:
            images: List of plate image arrays

        Returns:
            List of result dicts
        """
        return [self.read_plate(img) for img in images]


# ═══════════════════════════════════════════════════════════════════════════
#  Convenience function
# ═══════════════════════════════════════════════════════════════════════════

_global_reader = None

def get_plate_text(plate_image: np.ndarray) -> str:
    """
    Quick-use function — extract plate text from image.

    Returns:
        Plate number string (e.g. "KA05AB1234") or empty string if failed.
    """
    global _global_reader
    if _global_reader is None:
        _global_reader = OCRReader()

    result = _global_reader.read_plate(plate_image)
    return result["text"]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ParkPilot — OCR Reader Test")
    parser.add_argument("--image", required=True, help="Path to plate image")
    args = parser.parse_args()

    reader = OCRReader()
    img = cv2.imread(args.image)
    result = reader.read_plate(img)

    print(f"\n{'='*40}")
    print(f"  ParkPilot OCR Reader")
    print(f"{'='*40}")
    print(f"  Raw Text  : {result['raw_text']}")
    print(f"  Cleaned   : {result['text']}")
    print(f"  Confidence: {result['confidence']:.1%}")
    print(f"  Valid     : {result['valid']}")
    print(f"{'='*40}\n")
