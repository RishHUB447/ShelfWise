import pandas as pd
import numpy as np
from prophet import Prophet
from xgboost import XGBRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error
import pickle
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "data")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "saved_models")
os.makedirs(MODEL_PATH, exist_ok=True)

def load_and_preprocess(csv_filename):
    df = pd.read_csv(os.path.join(DATA_PATH, csv_filename))
    df['Date'] = pd.to_datetime(df['Date'])
    
    le = LabelEncoder()
    for col in ['Category', 'Region', 'Weather Condition', 'Seasonality']:
        df[col] = le.fit_transform(df[col].astype(str))
    
    df['Holiday/Promotion'] = df['Holiday/Promotion'].astype(int)
    df['Discount'] = df['Discount'].astype(float)
    return df

def train_prophet(df, product_id, store_id):
    subset = df[(df['Product ID'] == product_id) & (df['Store ID'] == store_id)].copy()
    subset = subset.rename(columns={'Date': 'ds', 'Units Sold': 'y'})
    
    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        seasonality_mode='multiplicative'
    )
    model.add_regressor('Weather Condition')
    model.add_regressor('Holiday/Promotion')
    model.add_regressor('Discount')
    model.add_regressor('Seasonality')
    
    model.fit(subset[['ds', 'y', 'Weather Condition', 'Holiday/Promotion', 'Discount', 'Seasonality']])
    return model

def train_xgboost(df):
    features = ['Category', 'Region', 'Inventory Level', 'Price', 
                'Discount', 'Weather Condition', 'Holiday/Promotion', 
                'Competitor Pricing', 'Seasonality']
    
    X = df[features]
    y = df['Units Sold']
    
    model = XGBRegressor(n_estimators=200, learning_rate=0.05, max_depth=6, random_state=42)
    model.fit(X, y)
    
    with open(os.path.join(MODEL_PATH, "xgboost_model.pkl"), "wb") as f:
        pickle.dump(model, f)
    
    return model

def evaluate(model, X, y_true):
    y_pred = model.predict(X)
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    return {"MAE": round(mae, 2), "RMSE": round(rmse, 2)}