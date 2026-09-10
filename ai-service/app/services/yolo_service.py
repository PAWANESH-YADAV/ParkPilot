import cv2
from ultralytics import YOLO
import numpy as np


class VehicleDetector:
    def __init__(self):
        self.model = YOLO("yolov8n.pt")
        self.vehicle_classes = ["car", "motorcycle", "bus", "truck"]

    def detect(self, image: np.ndarray):
        results = self.model(image, verbose=False)
        
        detections = []
        for result in results:
            for box in result.boxes:
                cls_id = int(box.cls[0])
                class_name = self.model.names[cls_id]
                if class_name in self.vehicle_classes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    confidence = float(box.conf[0])
                    detections.append({
                        "class": class_name,
                        "confidence": confidence,
                        "bbox": [x1, y1, x2, y2]
                    })
        
        return {
            "success": True,
            "count": len(detections),
            "detections": detections
        }

    def detect_from_video(self, video_path: str):
        cap = cv2.VideoCapture(video_path)
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            results = self.detect(frame)
            yield results
        cap.release()
