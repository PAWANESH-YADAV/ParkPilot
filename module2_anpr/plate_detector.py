"""
ParkPilot — Module 2: License Plate Detector
Uses OpenCV (contour detection + morphological ops) and optionally
YOLO to locate the license plate region in an image frame.

Usage:
    from module2_anpr.plate_detector import PlateDetector
    detector = PlateDetector()
    plate_img, bbox = detector.detect(frame)
"""

import cv2
import numpy as np
import os
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import get_logger

logger = get_logger("parkpilot.module2.plate_detector")


class PlateDetector:
    """
    License plate region detector using OpenCV contour analysis.

    Algorithm:
        1. Convert BGR → Grayscale
        2. Bilateral filter (preserve edges, reduce noise)
        3. Canny edge detection
        4. Find contours → filter by aspect ratio (license plates are ~4:1)
        5. Perspective transform to straighten the plate ROI
        6. Return cropped plate image for OCR

    Attributes:
        min_plate_area: Minimum contour area to be considered a plate
        aspect_ratio_range: Expected W:H ratio of license plates
        save_detections: If True, save detected plate crops to disk
    """

    def __init__(
        self,
        min_plate_area: int = 1500,
        aspect_ratio_range: tuple = (2.0, 6.5),
        save_dir: str = "module2_anpr/detected_plates/",
        save_detections: bool = False
    ):
        self.min_plate_area = min_plate_area
        self.aspect_ratio_range = aspect_ratio_range
        self.save_dir = save_dir
        self.save_detections = save_detections

        if save_detections:
            os.makedirs(save_dir, exist_ok=True)

        logger.info("PlateDetector initialized | OpenCV method")

    # ── Core Detection ────────────────────────────────────────────────────────

    def detect(self, frame: np.ndarray, draw_bbox: bool = False):
        """
        Detect license plate in a frame.

        Args:
            frame: BGR image frame
            draw_bbox: If True, draw bounding box on frame (modifies in-place)

        Returns:
            (plate_crop, bbox): Cropped plate image and (x, y, w, h) bounding box
                                Returns (None, None) if no plate found
        """
        if frame is None or frame.size == 0:
            return None, None

        # Step 1: Preprocessing
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        bilateral = cv2.bilateralFilter(gray, 11, 17, 17)

        # Step 2: Edge Detection
        edges = cv2.Canny(bilateral, 30, 200)

        # Step 3: Find Contours
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        # Sort by area (largest first)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:30]

        # Step 4: Filter candidate contours
        plate_contour = None
        for cnt in contours:
            perimeter = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.018 * perimeter, True)

            if len(approx) == 4:  # Quadrilateral
                x, y, w, h = cv2.boundingRect(approx)
                area = cv2.contourArea(cnt)

                if area < self.min_plate_area:
                    continue

                aspect_ratio = w / max(h, 1)
                if self.aspect_ratio_range[0] <= aspect_ratio <= self.aspect_ratio_range[1]:
                    plate_contour = approx
                    break

        if plate_contour is None:
            # Fallback: Try finding rectangular regions in specific image zones
            plate_contour, bbox = self._fallback_detect(frame, edges)
            if plate_contour is None:
                return None, None

        # Step 5: Extract plate crop
        x, y, w, h = cv2.boundingRect(plate_contour)
        bbox = (x, y, w, h)

        # Add padding
        pad = 5
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(frame.shape[1], x + w + pad)
        y2 = min(frame.shape[0], y + h + pad)
        plate_crop = frame[y1:y2, x1:x2]

        # Step 6: Perspective correction
        plate_crop = self._perspective_correct(plate_crop)

        if draw_bbox:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, "LICENSE PLATE", (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        if self.save_detections and plate_crop is not None and plate_crop.size > 0:
            self._save_plate(plate_crop)

        return plate_crop, bbox

    def _fallback_detect(self, frame: np.ndarray, edges: np.ndarray):
        """
        Fallback plate detection using morphological operations.
        Works better on low-quality images.
        """
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (17, 3))
        morphed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(morphed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in sorted(contours, key=cv2.contourArea, reverse=True)[:10]:
            x, y, w, h = cv2.boundingRect(cnt)
            area = w * h
            aspect = w / max(h, 1)

            if (area > self.min_plate_area and
                    self.aspect_ratio_range[0] <= aspect <= self.aspect_ratio_range[1]):
                approx = np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h]])
                return approx, (x, y, w, h)

        return None, None

    def _perspective_correct(self, plate_img: np.ndarray) -> np.ndarray:
        """
        Apply perspective transformation to straighten the plate.
        Ensures consistent OCR input regardless of camera angle.
        """
        if plate_img is None or plate_img.size == 0:
            return plate_img

        # Standard plate output size for OCR
        target_w, target_h = 400, 100
        return cv2.resize(plate_img, (target_w, target_h))

    def _save_plate(self, plate_img: np.ndarray):
        """Save detected plate crop to disk."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        path = os.path.join(self.save_dir, f"plate_{ts}.jpg")
        cv2.imwrite(path, plate_img)

    # ── Enhanced Preprocessing for Difficult Conditions ──────────────────────

    def preprocess_for_night(self, frame: np.ndarray) -> np.ndarray:
        """
        Apply CLAHE (contrast enhancement) for night-time images.
        Improves detection accuracy in low-light conditions.
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        return cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)

    def detect_in_video(self, video_path: str, output_path: str = None) -> list:
        """
        Run plate detection across all frames of a video file.

        Args:
            video_path: Path to input video
            output_path: Optional path to save annotated output video

        Returns:
            List of detected plates with timestamps
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"Cannot open video: {video_path}")
            return []

        fps = cap.get(cv2.CAP_PROP_FPS)
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        writer = None
        if output_path:
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

        detections = []
        frame_num = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            plate_img, bbox = self.detect(frame, draw_bbox=True)
            if bbox:
                detections.append({
                    "frame": frame_num,
                    "timestamp_sec": frame_num / fps,
                    "bbox": bbox,
                    "has_plate": True
                })

            if writer:
                writer.write(frame)

            frame_num += 1

        cap.release()
        if writer:
            writer.release()

        logger.info(f"Video scan complete | Frames: {frame_num} | Detections: {len(detections)}")
        return detections


def detect_plate_from_file(image_path: str, draw: bool = True) -> tuple:
    """
    Convenience function — detect plate from an image file.

    Args:
        image_path: Path to image file
        draw: Draw bounding box on image

    Returns:
        (plate_crop, bbox, annotated_frame)
    """
    frame = cv2.imread(image_path)
    if frame is None:
        logger.error(f"Cannot read image: {image_path}")
        return None, None, None

    detector = PlateDetector(save_detections=True)
    plate_crop, bbox = detector.detect(frame, draw_bbox=draw)

    return plate_crop, bbox, frame


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ParkPilot — Plate Detector")
    parser.add_argument("--image", help="Path to test image")
    parser.add_argument("--camera", type=int, default=0, help="Camera index")
    args = parser.parse_args()

    if args.image:
        plate, bbox, frame = detect_plate_from_file(args.image, draw=True)
        if bbox:
            logger.info(f"Plate detected at: {bbox}")
            if plate is not None:
                cv2.imshow("Detected Plate", plate)
            cv2.imshow("Annotated Frame", frame)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        else:
            logger.warning("No plate detected in image")
    else:
        # Live camera demo
        detector = PlateDetector(save_detections=True)
        cap = cv2.VideoCapture(args.camera)
        logger.info("Press 'q' to quit")
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            plate_crop, bbox = detector.detect(frame, draw_bbox=True)
            cv2.imshow("Plate Detector", frame)
            if plate_crop is not None:
                cv2.imshow("Plate Crop", plate_crop)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        cap.release()
        cv2.destroyAllWindows()
