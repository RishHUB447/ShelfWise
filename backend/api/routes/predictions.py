from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from models import Prediction, Inventory, Product
import pickle
import numpy as np
import os
from datetime import datetime
from pydantic import BaseModel

router = APIRouter(prefix="/predictions", tags=["Predictions"])

MODEL_PATH = os.path.join(os.path.dirname(__file__), "../../ml/saved_models/xgboost_model.pkl")

def load_model():
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)

CATEGORY_MAP = {"Clothing": 0, "Electronics": 1, "Furniture": 2, "Groceries": 3, "Toys": 4}
REGION_MAP = {"East": 0, "North": 1, "South": 2, "West": 3}
WEATHER_MAP = {"Cloudy": 0, "Rainy": 1, "Snowy": 2, "Sunny": 3}
SEASON_MAP = {"Autumn": 0, "Spring": 1, "Summer": 2, "Winter": 3}

class PredictionRequest(BaseModel):
    product_id: str
    store_id: str
    category: str
    region: str
    inventory_level: int
    price: float
    discount: float
    weather_condition: str
    holiday_promotion: bool
    competitor_pricing: float
    seasonality: str

@router.post("/predict")
def predict(req: PredictionRequest, db: Session = Depends(get_db)):
    try:
        model = load_model()

        features = np.array([[
            CATEGORY_MAP.get(req.category, 0),
            REGION_MAP.get(req.region, 0),
            req.inventory_level,
            req.price,
            req.discount,
            WEATHER_MAP.get(req.weather_condition, 0),
            int(req.holiday_promotion),
            req.competitor_pricing,
            SEASON_MAP.get(req.seasonality, 0)
        ]])

        predicted_units = float(model.predict(features)[0])
        confidence_score = round(min(100, max(0, 100 - (abs(predicted_units) / 10))), 2)
        restock_recommended = predicted_units > req.inventory_level * 0.7

        prediction = Prediction(
            product_id=req.product_id,
            store_id=req.store_id,
            predicted_units=round(predicted_units, 2),
            confidence_score=confidence_score,
            restock_recommended=restock_recommended,
            predicted_for_date=datetime.utcnow()
        )
        db.add(prediction)
        db.commit()
        db.refresh(prediction)

        return {
            "product_id": req.product_id,
            "store_id": req.store_id,
            "predicted_units": round(predicted_units, 2),
            "confidence_score": confidence_score,
            "restock_recommended": restock_recommended,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{product_id}")
def get_prediction_history(product_id: str, db: Session = Depends(get_db)):
    predictions = db.query(Prediction).filter(Prediction.product_id == product_id).all()
    return predictions