"""
FastAPI ML Service Integration.
Handles communication with the ML inference service.
"""

import requests
from django.conf import settings
from typing import Dict, Optional

from .crop_catalog import get_crop_catalog_entry


class MLServiceClient:
    """
    Client for FastAPI ML Service.
    """
    
    def __init__(self):
        self.base_url = settings.FASTAPI_ML_SERVICE_URL
        self.predict_endpoint = f"{self.base_url}/predict/"
        self.timeout = 10  # seconds
    
    def predict_disease(
        self, 
        image_url: str, 
        farmer_location: Optional[str] = None,
        region_code: Optional[str] = None
    ) -> Dict:
        """
        Send image URL to ML service for disease prediction.
        
        Args:
            image_url: URL of the uploaded image
            farmer_location: Location of the farmer
            region_code: Region code for vendor recommendations
            
        Returns:
            dict: ML service response containing:
                - disease_name: str
                - disease_confidence: float (0-1)
                - treatment_recommendation: dict
                - vendor_info: list
                - ml_model_version: str
        """
        
        payload = {
            "image_url": image_url,
            "metadata": {
                "location": farmer_location,
                "region_code": region_code
            }
        }
        
        try:
            response = requests.post(
                self.predict_endpoint,
                json=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.ConnectionError:
            raise Exception(
                f"Could not connect to ML service at {self.base_url}. "
                "Please ensure the FastAPI service is running."
            )
        except requests.exceptions.Timeout:
            raise Exception(
                f"ML service request timed out after {self.timeout} seconds"
            )
        except requests.exceptions.HTTPError as e:
            raise Exception(
                f"ML service returned error: {e.response.status_code} - {e.response.text}"
            )
        except Exception as e:
            raise Exception(f"ML service error: {str(e)}")
    
    def health_check(self) -> bool:
        """
        Check if ML service is available.
        
        Returns:
            bool: True if service is healthy
        """
        try:
            health_url = f"{self.base_url}/health"
            response = requests.get(health_url, timeout=5)
            if response.status_code != 200:
                return False

            payload = response.json()
            return (
                payload.get("status") == "healthy"
                and payload.get("model_type") == "YOLOv8"
                and payload.get("model_loaded") is True
            )
        except:
            return False
    
    def get_model_info(self) -> Optional[Dict]:
        """
        Get information about the ML model.
        
        Returns:
            dict: Model information including version, accuracy, etc.
        """
        try:
            info_url = f"{self.base_url}/model/info"
            response = requests.get(info_url, timeout=5)
            
            if response.status_code == 200:
                return response.json()
            return None
            
        except:
            return None


class MockMLServiceClient(MLServiceClient):
    """
    Mock ML service for testing when FastAPI service is not available.
    """
    
    def predict_disease(
        self, 
        image_url: str, 
        farmer_location: Optional[str] = None,
        region_code: Optional[str] = None
    ) -> Dict:
        """
        Return mock prediction for testing.
        """
        
        disease_name = "Maize leaf blight"
        treatment = get_crop_catalog_entry(disease_name)["treatments"][0]

        return {
            "disease_name": disease_name,
            "disease_confidence": 0.87,
            "treatment_recommendation": {
                "medicine": treatment["medicine_name"],
                "active_ingredient": treatment["active_ingredient"],
                "dosage": treatment["dosage"],
                "application_method": treatment["application_method"],
                "frequency": treatment["frequency"],
                "duration": treatment["duration"],
                "precautions": treatment["precautions"],
                "effectiveness_rating": treatment["effectiveness_rating"],
            },
            "top_predictions": [
                {"disease": "Maize leaf blight", "confidence": 0.87},
                {"disease": "Maize leaf spot", "confidence": 0.08},
                {"disease": "Maize streak virus", "confidence": 0.03},
                {"disease": "Maize healthy", "confidence": 0.01},
                {"disease": "Maize leaf beetle", "confidence": 0.01},
            ],
            "is_healthy": False,
            "severity": "Medium confidence - Monitor closely",
            "vendor_info": [],
            "ml_model_version": "v1.0-mock"
        }
    
    def health_check(self) -> bool:
        return True
    
    def get_model_info(self) -> Optional[Dict]:
        return {
            "model_version": "v1.0-mock",
            "model_type": "CNN",
            "accuracy": 0.85,
            "classes": ["Maize Rust", "Maize Leaf Blight", "Healthy"]
        }
