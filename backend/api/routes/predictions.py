from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from models import Product, SalesLog, Prediction, Alert
from ml.model import run_prediction
from datetime import datetime

router = APIRouter(prefix="/predictions", tags=["Predictions"])

@router.get("/run/{product_id}")
def run_product_prediction(product_id: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    sales_logs = db.query(SalesLog).filter(
        SalesLog.product_id == product_id
    ).order_by(SalesLog.date).all()

    result = run_prediction(sales_logs, product.current_stock, product.reorder_point)

    prediction = Prediction(
        product_id=product_id,
        shop_id=product.shop_id,
        predicted_units_7d=float(result["predicted_units_7d"]),
        predicted_units_14d=float(result["predicted_units_14d"]),
        predicted_units_30d=float(result["predicted_units_30d"]),
        days_until_stockout=float(result["days_until_stockout"]),
        restock_recommended=bool(result["restock_recommended"]),
        restock_quantity=int(result["restock_quantity"]),
        confidence_score=float(result["confidence_score"]),
    )
    db.add(prediction)

    if result["restock_recommended"]:
        alert = Alert(
            shop_id=product.shop_id,
            product_id=product_id,
            alert_type="restock",
            message=f"{product.name} will run out in {result['days_until_stockout']} days. Restock {result['restock_quantity']} units."
        )
        db.add(alert)

    db.commit()
    db.refresh(prediction)

    return {
        "product": product.name,
        "current_stock": product.current_stock,
        **result
    }

@router.get("/shop/{shop_id}")
def get_shop_predictions(shop_id: str, db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.shop_id == shop_id).all()
    results = []
    for product in products:
        latest = db.query(Prediction).filter(
            Prediction.product_id == product.id
        ).order_by(Prediction.created_at.desc()).first()
        if latest:
            results.append({
                "product_id": product.id,
                "product_name": product.name,
                "category": product.category,
                "current_stock": product.current_stock,
                "days_until_stockout": latest.days_until_stockout,
                "predicted_units_7d": latest.predicted_units_7d,
                "predicted_units_30d": latest.predicted_units_30d,
                "restock_recommended": latest.restock_recommended,
                "restock_quantity": latest.restock_quantity,
                "confidence_score": latest.confidence_score,
            })
    return results

@router.get("/alerts/{shop_id}")
def get_alerts(shop_id: str, db: Session = Depends(get_db)):
    alerts = db.query(Alert).filter(
        Alert.shop_id == shop_id,
        Alert.is_resolved == False
    ).order_by(Alert.created_at.desc()).all()
    return alerts

@router.patch("/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: str, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_resolved = True
    db.commit()
    return {"message": "Alert resolved"}