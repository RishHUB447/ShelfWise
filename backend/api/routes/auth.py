from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core.auth import hash_password, verify_password, create_token, get_current_shop
from models import Shop
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/auth", tags=["Auth"])

class RegisterData(BaseModel):
    shop_name: str
    owner_name: str
    email: str
    password: str

class LoginData(BaseModel):
    email: str
    password: str

@router.post("/register")
def register(data: RegisterData, db: Session = Depends(get_db)):
    existing = db.query(Shop).filter(Shop.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    shop = Shop(
        name=data.shop_name,
        owner_name=data.owner_name,
        email=data.email,
        password_hash=hash_password(data.password)
    )
    db.add(shop)
    db.commit()
    db.refresh(shop)

    token = create_token({"shop_id": shop.id})
    return {
        "token": token,
        "shop": {
            "id": shop.id,
            "name": shop.name,
            "owner_name": shop.owner_name,
            "email": shop.email
        }
    }

@router.post("/login")
def login(data: LoginData, db: Session = Depends(get_db)):
    shop = db.query(Shop).filter(Shop.email == data.email).first()
    if not shop or not verify_password(data.password, shop.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_token({"shop_id": shop.id})
    return {
        "token": token,
        "shop": {
            "id": shop.id,
            "name": shop.name,
            "owner_name": shop.owner_name,
            "email": shop.email
        }
    }

@router.get("/me")
def me(db: Session = Depends(get_db), token: str = None):
    pass

@router.delete("/delete-account")
def delete_account(db: Session = Depends(get_db), shop: Shop = Depends(get_current_shop)):
    from models import Product, SalesLog, Prediction, Alert
    
    # delete in order to respect foreign keys
    products = db.query(Product).filter(Product.shop_id == shop.id).all()
    for p in products:
        db.query(SalesLog).filter(SalesLog.product_id == p.id).delete()
        db.query(Prediction).filter(Prediction.product_id == p.id).delete()
        db.query(Alert).filter(Alert.product_id == p.id).delete()
    
    db.query(Product).filter(Product.shop_id == shop.id).delete()
    db.query(Alert).filter(Alert.shop_id == shop.id).delete()
    db.delete(shop)
    db.commit()
    
    return {"message": "Account deleted successfully"}