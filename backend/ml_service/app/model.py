"""
YOLOv8 disease prediction model handler.
"""

import logging
import os
from pathlib import Path
from typing import Dict

from PIL import Image
from ultralytics import YOLO

logger = logging.getLogger(__name__)


class DiseasePredictor:
    """Runs crop disease prediction using a trained YOLOv8 classification model."""

    def __init__(self, model_path: str = None, class_names_path: str = None):
        self.project_root = Path(__file__).resolve().parents[3]
        self.model_path = self._resolve_model_path(model_path)
        self.class_names_path = class_names_path or str(self.project_root / "data" / "class_names.txt")
        self.model = None
        self.class_names = []

        self.treatments = {
            "Cashew anthracnose": {
                "medicine": "Copper-based fungicide",
                "dosage": "Follow product label rate",
                "application_method": "Foliar spray",
                "frequency": "Every 7-10 days during active infection",
                "precautions": "Prune affected parts and avoid spraying during rain",
            },
            "Cashew gumosis": {
                "medicine": "Copper fungicide and sanitation",
                "dosage": "Follow product label rate",
                "application_method": "Clean infected bark and apply protective treatment",
                "frequency": "Monitor weekly",
                "precautions": "Avoid stem injuries and improve drainage",
            },
            "Cashew leaf miner": {
                "medicine": "Recommended systemic insecticide",
                "dosage": "Follow local extension guidance",
                "application_method": "Target affected leaves",
                "frequency": "Repeat only if infestation persists",
                "precautions": "Avoid spraying during flowering where pollinators are active",
            },
            "Cashew red rust": {
                "medicine": "Copper oxychloride",
                "dosage": "Follow product label rate",
                "application_method": "Foliar spray",
                "frequency": "Every 10-14 days",
                "precautions": "Remove severely affected leaves",
            },
            "Cassava bacterial blight": {
                "medicine": "Field sanitation and disease-free cuttings",
                "dosage": "N/A",
                "application_method": "Remove infected plants and avoid contaminated tools",
                "frequency": "Ongoing monitoring",
                "precautions": "Use resistant varieties where available",
            },
            "Cassava brown spot": {
                "medicine": "Mancozeb or copper-based fungicide",
                "dosage": "Follow product label rate",
                "application_method": "Foliar spray",
                "frequency": "Every 10-14 days",
                "precautions": "Improve spacing and remove infected leaves",
            },
            "Cassava green mite": {
                "medicine": "Miticide or biological control",
                "dosage": "Follow product label rate",
                "application_method": "Target underside of leaves",
                "frequency": "As infestation requires",
                "precautions": "Avoid overuse of broad-spectrum insecticides",
            },
            "Cassava mosaic": {
                "medicine": "No chemical cure - management only",
                "dosage": "N/A",
                "application_method": "Remove infected plants and use disease-free cuttings",
                "frequency": "Regular field monitoring",
                "precautions": "Control whiteflies and plant resistant varieties",
            },
            "Maize fall armyworm": {
                "medicine": "Emamectin benzoate or recommended biopesticide",
                "dosage": "Follow product label rate",
                "application_method": "Apply into maize whorl",
                "frequency": "Scout twice weekly and treat early",
                "precautions": "Rotate active ingredients to reduce resistance",
            },
            "Maize grasshoper": {
                "medicine": "Recommended contact insecticide",
                "dosage": "Follow product label rate",
                "application_method": "Foliar spray at early infestation",
                "frequency": "As needed after scouting",
                "precautions": "Protect beneficial insects where possible",
            },
            "Maize leaf beetle": {
                "medicine": "Recommended contact or systemic insecticide",
                "dosage": "Follow product label rate",
                "application_method": "Foliar spray",
                "frequency": "As needed after scouting",
                "precautions": "Treat only when economic damage is visible",
            },
            "Maize leaf blight": {
                "medicine": "Mancozeb Fungicide",
                "dosage": "2.5 kg per hectare",
                "application_method": "Foliar spray",
                "frequency": "Every 7-10 days",
                "precautions": "Avoid spraying during rain and use protective equipment",
            },
            "Maize leaf spot": {
                "medicine": "Azoxystrobin or Mancozeb",
                "dosage": "Follow product label rate",
                "application_method": "Foliar spray",
                "frequency": "Every 10-14 days",
                "precautions": "Improve spacing and rotate crops",
            },
            "Maize streak virus": {
                "medicine": "Vector management and infected plant removal",
                "dosage": "Use recommended insecticide label rate for leafhopper control",
                "application_method": "Remove infected plants and control insect vectors",
                "frequency": "Monitor weekly",
                "precautions": "Use resistant varieties and avoid moving infected plant material",
            },
            "Tomato leaf blight": {
                "medicine": "Chlorothalonil or Mancozeb",
                "dosage": "2 kg per hectare",
                "application_method": "Foliar spray",
                "frequency": "Every 7 days",
                "precautions": "Remove infected leaves and avoid overhead irrigation",
            },
            "Tomato leaf curl": {
                "medicine": "Whitefly control and infected plant removal",
                "dosage": "Follow insecticide label rate",
                "application_method": "Control whitefly vectors and rogue infected plants",
                "frequency": "Monitor weekly",
                "precautions": "Use resistant seedlings where available",
            },
            "Tomato septoria leaf spot": {
                "medicine": "Copper fungicide or Chlorothalonil",
                "dosage": "Follow product label rate",
                "application_method": "Foliar spray",
                "frequency": "Every 7-10 days",
                "precautions": "Remove lower infected leaves and mulch soil",
            },
            "Tomato_verticulium_wilt": {
                "medicine": "No curative chemical treatment",
                "dosage": "N/A",
                "application_method": "Remove infected plants and rotate crops",
                "frequency": "Season-long management",
                "precautions": "Use resistant varieties and avoid planting tomato repeatedly in same soil",
            },
            "Healthy": {
                "medicine": "No treatment needed",
                "dosage": "N/A",
                "application_method": "Continue regular crop care",
                "frequency": "N/A",
                "precautions": "Maintain good agricultural practices",
            },
        }

        self.load_model()
        self.load_class_names()

    def _resolve_model_path(self, model_path: str = None) -> str:
        candidates = []

        if model_path:
            candidates.append(Path(model_path))

        env_path = os.getenv("YOLO_MODEL_PATH")
        if env_path:
            candidates.append(Path(env_path))

        candidates.extend([
            self.project_root / "runs" / "classify" / "models" / "yolov8" / "train" / "weights" / "best.pt",
            self.project_root / "runs" / "classify" / "models" / "yolov8" / "train" / "weights" / "last.pt",
            self.project_root / "yolov8s-cls.pt",
            self.project_root / "models" / "best.pt",
        ])

        for candidate in candidates:
            resolved = candidate if candidate.is_absolute() else self.project_root / candidate
            if resolved.exists():
                return str(resolved)

        return str(candidates[0])

    def load_model(self):
        """Load trained YOLOv8 model."""
        if not os.path.exists(self.model_path):
            logger.error("YOLOv8 model file not found: %s", self.model_path)
            self.model = None
            return

        self.model = YOLO(self.model_path)
        logger.info("YOLOv8 model loaded from %s", self.model_path)

    def load_class_names(self):
        """Load class names from the YOLO model, class file, or fallback dataset names."""
        if self.model is not None and getattr(self.model, "names", None):
            names = self.model.names
            self.class_names = [names[index] for index in sorted(names)] if isinstance(names, dict) else list(names)
            logger.info("Loaded %s class names from YOLO model", len(self.class_names))
            return

        if os.path.exists(self.class_names_path):
            with open(self.class_names_path, "r", encoding="utf-8") as file:
                self.class_names = [
                    line.strip().split("\t", 1)[1] if "\t" in line else line.strip()
                    for line in file
                    if line.strip()
                ]
            logger.info("Loaded %s class names from %s", len(self.class_names), self.class_names_path)
            return

        self.class_names = [
            "Cashew anthracnose", "Cashew gumosis", "Cashew healthy",
            "Cashew leaf miner", "Cashew red rust", "Cassava bacterial blight",
            "Cassava brown spot", "Cassava green mite", "Cassava healthy",
            "Cassava mosaic", "Maize fall armyworm", "Maize grasshoper",
            "Maize healthy", "Maize leaf beetle", "Maize leaf blight",
            "Maize leaf spot", "Maize streak virus", "Tomato healthy",
            "Tomato leaf blight", "Tomato leaf curl", "Tomato septoria leaf spot",
            "Tomato_verticulium_wilt",
        ]

    def predict(self, image: Image.Image, top_k: int = 5) -> Dict:
        """Predict disease from a PIL image."""
        if self.model is None:
            raise RuntimeError(f"YOLOv8 model is not loaded. Expected weights at {self.model_path}")

        results = self.model(image.convert("RGB"), verbose=False)
        probs = results[0].probs

        top_class_idx = int(probs.top1)
        top_confidence = float(probs.top1conf)
        disease_name = self._class_name(top_class_idx)

        top_predictions = []
        top_indices = probs.top5[:top_k]
        top_confidences = probs.top5conf[:top_k].cpu().numpy()

        for index, confidence in zip(top_indices, top_confidences):
            top_predictions.append({
                "disease": self._class_name(int(index)),
                "confidence": float(confidence),
            })

        logger.info("Prediction: %s (%.2f%%)", disease_name, top_confidence * 100)

        return {
            "disease_name": disease_name,
            "confidence": top_confidence,
            "top_predictions": top_predictions,
            "is_healthy": "healthy" in disease_name.lower(),
        }

    def _class_name(self, index: int) -> str:
        if 0 <= index < len(self.class_names):
            return self.class_names[index]
        return f"Class_{index}"

    def get_treatment_recommendation(self, disease_name: str) -> Dict:
        """Return treatment recommendation for a predicted disease."""
        if disease_name in self.treatments:
            return self.treatments[disease_name]

        disease_lower = disease_name.lower().replace("_", " ")
        for key, treatment in self.treatments.items():
            normalized_key = key.lower().replace("_", " ")
            if normalized_key in disease_lower or disease_lower in normalized_key:
                return treatment

        if "healthy" in disease_lower:
            return self.treatments["Healthy"]

        return {
            "medicine": "Consult agricultural expert",
            "dosage": "Professional assessment required",
            "application_method": "Seek expert guidance",
            "frequency": "N/A",
            "precautions": "Document symptoms and contact an extension officer",
        }

    def get_severity_level(self, confidence: float) -> str:
        """Determine confidence severity text."""
        return self.get_prediction_confidence_text(confidence)

    def get_prediction_confidence_text(self, confidence: float) -> str:
        """Return confidence guidance without assuming every prediction is disease."""
        if confidence >= 0.9:
            return "High confidence"
        if confidence >= 0.75:
            return "Medium confidence"
        return "Low confidence - Consider expert consultation"
