from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base
from datetime import datetime

class Store(Base):
    __tablename__ = "stores"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    region = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    products = relationship("Product", back_populates="store")

class Product(Base):
    __tablename__ = "products"
    id = Column(String, primary_key=True)
    store_id = Column(String, ForeignKey("stores.id"))
    name = Column(String, nullable=False)
    category = Column(String)
    price = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    store = relationship("Store", back_populates="products")
    inventory = relationship("Inventory", back_populates="product")

class Inventory(Base):
    __tablename__ = "inventory"
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String, ForeignKey("products.id"))
    date = Column(DateTime, nullable=False)
    inventory_level = Column(Integer)
    units_sold = Column(Integer)
    units_ordered = Column(Integer)
    price = Column(Float)
    discount = Column(Float)
    weather_condition = Column(String)
    holiday_promotion = Column(Boolean, default=False)
    competitor_pricing = Column(Float)
    seasonality = Column(String)
    product = relationship("Product", back_populates="inventory")

class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String, ForeignKey("products.id"))
    store_id = Column(String)
    predicted_units = Column(Float)
    confidence_score = Column(Float)
    restock_recommended = Column(Boolean, default=False)
    predicted_for_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String, ForeignKey("products.id"))
    store_id = Column(String)
    alert_type = Column(String)
    message = Column(String)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)