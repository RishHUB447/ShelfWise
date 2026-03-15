import os
import pickle
from model import load_and_preprocess, train_xgboost, evaluate

CSV_FILE = "retail_store_inventory.csv"
MODEL_PATH = os.path.join(os.path.dirname(__file__), "saved_models")

def main():
    print("Loading dataset...")
    df = load_and_preprocess(CSV_FILE)
    print(f"Dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")

    print("Training XGBoost model...")
    features = ['Category', 'Region', 'Inventory Level', 'Price',
                'Discount', 'Weather Condition', 'Holiday/Promotion',
                'Competitor Pricing', 'Seasonality']
    
    X = df[features]
    y = df['Units Sold']
    
    model = train_xgboost(df)
    metrics = evaluate(model, X, y)
    
    print(f"Training complete!")
    print(f"MAE: {metrics['MAE']}")
    print(f"RMSE: {metrics['RMSE']}")
    print(f"Model saved to saved_models/xgboost_model.pkl")

if __name__ == "__main__":
    main()