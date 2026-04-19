from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from core.database import Base
from datetime import datetime
import uuid

def gen_id():
    return str(uuid.uuid4())

class Shop(Base):
    __tablename__ = "shops"
    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    owner_name = Column(String)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    products = relationship("Product", back_populates="shop")

class Product(Base):
    __tablename__ = "products"
    id = Column(String, primary_key=True, default=gen_id)
    shop_id = Column(String, ForeignKey("shops.id"), nullable=False)
    name = Column(String, nullable=False)
    category = Column(String)
    price = Column(Float)
    current_stock = Column(Integer, default=0)
    reorder_point = Column(Integer, default=20)
    created_at = Column(DateTime, default=datetime.utcnow)
    shop = relationship("Shop", back_populates="products")
    sales = relationship("SalesLog", back_populates="product")
    predictions = relationship("Prediction", back_populates="product")

class SalesLog(Base):
    __tablename__ = "sales_logs"
    id = Column(String, primary_key=True, default=gen_id)
    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    shop_id = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)
    units_sold = Column(Integer, nullable=False)
    stock_remaining = Column(Integer)
    discount_active = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    product = relationship("Product", back_populates="sales")
    
class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(String, primary_key=True, default=gen_id)
    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    shop_id = Column(String, nullable=False)
    predicted_units_7d = Column(Float)
    predicted_units_14d = Column(Float)
    predicted_units_30d = Column(Float)
    days_until_stockout = Column(Float)
    restock_recommended = Column(Boolean, default=False)
    restock_quantity = Column(Integer)
    confidence_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    product = relationship("Product", back_populates="predictions")

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(String, primary_key=True, default=gen_id)
    shop_id = Column(String, nullable=False)
    product_id = Column(String, ForeignKey("products.id"))
    alert_type = Column(String)
    message = Column(Text)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

