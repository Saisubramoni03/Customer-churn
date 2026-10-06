import sys
import os
from fastapi import APIRouter
from fastapi import Depends
from database.security import verify_api_key

from schemas.prediction import (
    ChurnPredictionRequest,
    ChurnPredictionResponse,
)

from database.logger import logger

# Import ML prediction from phase6
PHASE6_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "phase6")
if PHASE6_DIR not in sys.path:
    sys.path.insert(0, PHASE6_DIR)

try:
    from predict import predict_churn as ml_predict_churn
except ImportError:
    logger.warning("Could not import ML model from phase6")
    ml_predict_churn = None

router = APIRouter(
    tags=["Prediction"]
)


@router.post(
    "/predict-churn",
    response_model=ChurnPredictionResponse,
)
def predict_churn(
    request: ChurnPredictionRequest,
    _: None = Depends(verify_api_key),
):
    logger.info(
        f"POST /predict-churn customer={request.customer_id}"
    )
    
    try:
        if ml_predict_churn:
            # Use real ML model from phase6
            result = ml_predict_churn(
                tenure=request.tenure,
                monthly_charges=request.monthly_charges,
                contract_type=request.contract_type,
                service_count=request.service_count
            )
            return {
                "customer_id": request.customer_id or "N/A",
                "risk_score": result.get("risk_score", 0.0),
                "prediction": result.get("prediction", "Unable to predict"),
                "confidence": result.get("confidence", 0.0)
            }
        else:
            # Fallback if model not available
            logger.warning("ML model not loaded, using default prediction")
            return {
                "customer_id": request.customer_id or "N/A",
                "risk_score": 0.5,
                "prediction": "Model unavailable",
                "confidence": 0.0
            }
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        return {
            "customer_id": request.customer_id or "N/A",
            "risk_score": 0.5,
            "prediction": "Error during prediction",
            "confidence": 0.0
        }