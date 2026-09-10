import cv2
import numpy as np
import easyocr


class ANPRService:
    def __init__(self):
        self.reader = easyocr.Reader(['en'])

    def preprocess_image(self, image: np.ndarray):
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(blurred, 50, 150)
        return edged

    def detect_and_recognize(self, image: np.ndarray):
        try:
            results = self.reader.readtext(image)
            
            best_plate = None
            best_confidence = 0.0
            
            for (bbox, text, confidence) in results:
                if confidence > best_confidence and self.is_valid_plate(text):
                    best_plate = text
                    best_confidence = confidence
            
            return {
                "license_plate": best_plate,
                "confidence": best_confidence,
                "success": best_plate is not None
            }
        except Exception as e:
            return {
                "license_plate": None,
                "confidence": 0.0,
                "success": False,
                "error": str(e)
            }

    def is_valid_plate(self, text: str) -> bool:
        text = text.replace(" ", "").replace("-", "").upper()
        return len(text) >= 4 and any(c.isdigit() for c in text)
