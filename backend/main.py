from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.database import engine, Base
import models
from api.routes import inventory, predictions, auth

Base.metadata.create_all(bind=engine)

app = FastAPI(title="ShelfWise API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://*.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(inventory.router)
app.include_router(predictions.router)

@app.get("/")
def root():
    return {"message": "ShelfWise API is running!"}