from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from core.database import get_db
from models import Shop, Product, SalesLog
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import csv
import io

router = APIRouter(prefix="/inventory", tags=["Inventory"])

# --- Schemas ---
class ShopCreate(BaseModel):
    name: str
    owner_name: Optional[str] = None

class ProductCreate(BaseModel):
    shop_id: str
    name: str
    category: Optional[str] = "General"
    price: Optional[float] = 0.0
    current_stock: Optional[int] = 0
    reorder_point: Optional[int] = 20

class SalesEntry(BaseModel):
    product_id: str
    shop_id: str
    date: str
    units_sold: int
    stock_remaining: Optional[int] = None

# --- Shop Routes ---
@router.post("/shops")
def create_shop(data: ShopCreate, db: Session = Depends(get_db)):
    shop = Shop(name=data.name, owner_name=data.owner_name)
    db.add(shop)
    db.commit()
    db.refresh(shop)
    return shop

@router.get("/shops/{shop_id}")
def get_shop(shop_id: str, db: Session = Depends(get_db)):
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    return shop

# --- Product Routes ---
@router.post("/products")
def create_product(data: ProductCreate, db: Session = Depends(get_db)):
    product = Product(**data.dict())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

@router.get("/products/{shop_id}")
def get_products(shop_id: str, db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.shop_id == shop_id).all()
    return products

@router.patch("/products/{product_id}/stock")
def update_stock(product_id: str, stock: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.current_stock = stock
    db.commit()
    return {"message": "Stock updated", "current_stock": stock}

# --- Sales Log Routes ---
@router.post("/sales")
def log_sale(data: SalesEntry, db: Session = Depends(get_db)):
    log = SalesLog(
        product_id=data.product_id,
        shop_id=data.shop_id,
        date=datetime.strptime(data.date, "%Y-%m-%d"),
        units_sold=data.units_sold,
        stock_remaining=data.stock_remaining
    )
    db.add(log)
    product = db.query(Product).filter(Product.id == data.product_id).first()
    if product and data.stock_remaining is not None:
        product.current_stock = data.stock_remaining
    db.commit()
    return {"message": "Sale logged successfully"}

@router.get("/sales/{product_id}")
def get_sales(product_id: str, db: Session = Depends(get_db)):
    logs = db.query(SalesLog).filter(SalesLog.product_id == product_id).order_by(SalesLog.date).all()
    return logs

# --- CSV Upload ---
@router.post("/upload-csv/{shop_id}")
async def upload_csv(shop_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode("utf-8")))
    
    logs_added = 0
    products_created = 0

    for row in reader:
        name = row.get("product_name", "").strip()
        category = row.get("category", "General").strip()
        units_sold = int(row.get("units_sold", 0))
        stock_remaining = int(row.get("stock_remaining", 0))
        date_str = row.get("date", "").strip()

        if not name or not date_str:
            continue

        product = db.query(Product).filter(
            Product.shop_id == shop_id,
            Product.name == name
        ).first()

        if not product:
            product = Product(
                shop_id=shop_id,
                name=name,
                category=category,
                current_stock=stock_remaining
            )
            db.add(product)
            db.commit()
            db.refresh(product)
            products_created += 1

        log = SalesLog(
            product_id=product.id,
            shop_id=shop_id,
            date=datetime.strptime(date_str, "%Y-%m-%d"),
            units_sold=units_sold,
            stock_remaining=stock_remaining
        )
        db.add(log)
        product.current_stock = stock_remaining
        logs_added += 1

    db.commit()
    return {
        "message": "CSV uploaded successfully",
        "products_created": products_created,
        "sales_logs_added": logs_added
    }