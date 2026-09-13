"""
AgriGani ML Service - FastAPI Application with YOLOv8
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, List
import logging

try:
    from .model import DiseasePredictor
    from .utils import download_image
except ImportError:
    from model import DiseasePredictor
    from utils import download_image

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPPORTED_CROPS = ["Cashew", "Cassava", "Maize", "Tomato"]

# Initialize FastAPI app
app = FastAPI(
    title="AgriGani ML Service - YOLOv8",
    description="AI-powered crop disease prediction using YOLOv8",
    version="2.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize YOLOv8 predictor
predictor = DiseasePredictor()


class PredictionRequest(BaseModel):
    """Request model for disease prediction"""
    image_url: HttpUrl
    metadata: Optional[Dict] = {}


class TopPrediction(BaseModel):
    """Single prediction in top-k results"""
    disease: str
    confidence: float


class PredictionResponse(BaseModel):
    """Response model for disease prediction"""
    disease_name: str
    disease_confidence: float
    is_healthy: bool
    severity: str
    top_predictions: List[TopPrediction]
    treatment_recommendation: Dict
    vendor_info: List = []
    ml_model_version: str


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Agrigani ML Service - YOLOv8",
        "version": "2.0.0",
        "status": "running",
        "model": "YOLOv8s-cls"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": predictor.model is not None,
        "model_type": "YOLOv8",
        "classes_loaded": len(predictor.class_names),
        "supported_crops": SUPPORTED_CROPS,
    }


@app.get("/model/info")
async def model_info():
    """Get model information"""
    return {
        "model_version": "YOLOv8s-cls v2.0",
        "model_type": "YOLOv8 Classification",
        "framework": "Ultralytics",
        "input_size": [224, 224, 3],
        "classes": predictor.class_names,
        "num_classes": len(predictor.class_names),
        "supported_crops": SUPPORTED_CROPS,
        "test_accuracy": "~90%"  # Update with your actual accuracy
    }


@app.post("/predict/", response_model=PredictionResponse)
async def predict_disease(request: PredictionRequest):
    """
    Predict crop disease from image URL
    
    Args:
        request: PredictionRequest with image_url and metadata
        
    Returns:
        PredictionResponse with disease prediction and recommendations
    """
    try:
        logger.info(f" Received prediction request for: {request.image_url}")
        
        # Download image from URL
        image = download_image(str(request.image_url))
        
        # Get prediction from YOLOv8 model
        prediction = predictor.predict(image)
        
        # Get severity level
        severity = predictor.get_severity_level(prediction['confidence'])
        
        # Get treatment recommendation
        treatment = predictor.get_treatment_recommendation(prediction['disease_name'])
        
        response = PredictionResponse(
            disease_name=prediction['disease_name'],
            disease_confidence=prediction['confidence'],
            is_healthy=prediction.get('is_healthy', False),
            severity=severity,
            top_predictions=prediction.get('top_predictions', []),
            treatment_recommendation=treatment,
            vendor_info=[],  # Django backend handles vendor recommendations
            ml_model_version="YOLOv8s-cls-v2.0"
        )
        
        logger.info(f" Prediction: {prediction['disease_name']} ({prediction['confidence']:.2%})")
        
        return response
        
    except Exception as e:
        logger.error(f" Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
