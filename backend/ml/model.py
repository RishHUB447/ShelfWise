import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.preprocessing import LabelEncoder
import logging
from datetime import timedelta
import warnings
warnings.filterwarnings("ignore")

logging.getLogger("lightgbm").setLevel(logging.WARNING)

# -------------------------------------------------------------------
# 1. Helper: Build continuous daily time series per product
# -------------------------------------------------------------------
def build_product_ts(sales_logs, product_id=None):
    """
    Convert list of sales logs into a daily dataframe with zeros for missing days.
    """
    if not sales_logs:
        return pd.DataFrame(columns=['ds', 'y', 'discount_active', 'product_id'])
    
    df = pd.DataFrame([{
        'ds': pd.to_datetime(log.date),
        'y': float(log.units_sold),
        'discount_active': float(getattr(log, 'discount_active', 0) or 0),
        'product_id': product_id if product_id else getattr(log, 'product_id', 'unknown')
    } for log in sales_logs])
    
    # Ensure no negative sales
    df['y'] = df['y'].clip(lower=0)
    
    # Create full date range from min to max date
    date_range = pd.date_range(start=df['ds'].min(), end=df['ds'].max(), freq='D')
    
    # Reindex each product (groupby product_id if multiple)
    if df['product_id'].nunique() > 1:
        # Multiple products in one call – should not happen per our design, but handle gracefully
        full_df = []
        for pid, grp in df.groupby('product_id'):
            grp = grp.set_index('ds').reindex(date_range, fill_value=0).reset_index()
            grp.rename(columns={'index': 'ds'}, inplace=True)
            grp['y'] = grp['y'].fillna(0)
            grp['discount_active'] = grp['discount_active'].fillna(0)
            grp['product_id'] = pid
            full_df.append(grp)
        df = pd.concat(full_df, ignore_index=True)
    else:
        df = df.set_index('ds').reindex(date_range, fill_value=0).reset_index()
        df.rename(columns={'index': 'ds'}, inplace=True)
        df['y'] = df['y'].fillna(0)
        df['discount_active'] = df['discount_active'].fillna(0)
        if product_id:
            df['product_id'] = product_id
        else:
            df['product_id'] = df['product_id'].fillna('unknown')
    
    return df

# -------------------------------------------------------------------
# 2. Feature engineering
# -------------------------------------------------------------------
def add_time_features(df):
    """Add calendar and rolling features."""
    df = df.copy()
    df['dayofweek'] = df['ds'].dt.dayofweek
    df['dayofmonth'] = df['ds'].dt.day
    df['month'] = df['ds'].dt.month
    df['quarter'] = df['ds'].dt.quarter
    df['year'] = df['ds'].dt.year
    df['days_since_start'] = (df['ds'] - df['ds'].min()).dt.days
    
    # Indian seasons
    def get_season(month):
        if month in [3,4,5]: return 1   # Summer
        if month in [6,7,8,9]: return 2 # Monsoon
        if month in [10,11]: return 3   # Festive/Autumn
        return 0                         # Winter
    df['season'] = df['month'].apply(get_season)
    
    # Weekend flag
    df['is_weekend'] = (df['dayofweek'] >= 5).astype(int)
    
    # Lags (need to compute per product, but we'll assume single product per df)
    for lag in [1, 2, 3, 7, 14, 30]:
        df[f'lag_{lag}'] = df['y'].shift(lag)
    
    # Rolling statistics
    for window in [7, 14, 30]:
        df[f'rolling_mean_{window}'] = df['y'].rolling(window, min_periods=1).mean()
        df[f'rolling_std_{window}'] = df['y'].rolling(window, min_periods=1).std().fillna(0)
    
    # Exponential weighted moving average (trend)
    df['ewm_7'] = df['y'].ewm(span=7, adjust=False).mean()
    
    # Days since last positive sale
    df['days_since_sale'] = 0
    last_sale_day = -1
    for i, row in df.iterrows():
        if row['y'] > 0:
            last_sale_day = i
            df.at[i, 'days_since_sale'] = 0
        else:
            df.at[i, 'days_since_sale'] = i - last_sale_day if last_sale_day != -1 else 999
    
    # Fill NaN lags with 0
    lag_cols = [c for c in df.columns if 'lag_' in c]
    df[lag_cols] = df[lag_cols].fillna(0)
    
    return df

# -------------------------------------------------------------------
# 3. Train global LightGBM model across all products (if multiple)
# -------------------------------------------------------------------
def train_global_model(df_all_products):
    """
    df_all_products: concatenated data from all products with a 'product_id' column.
    Returns trained model, feature list, label encoder for product_id.
    """
    # Encode product_id
    le = LabelEncoder()
    df_all_products['product_encoded'] = le.fit_transform(df_all_products['product_id'].astype(str))
    
    # Define features
    feature_cols = [
        'dayofweek', 'dayofmonth', 'month', 'quarter', 'year', 'season', 'is_weekend',
        'days_since_start', 'days_since_sale', 'discount_active', 'product_encoded',
        'lag_1', 'lag_2', 'lag_3', 'lag_7', 'lag_14', 'lag_30',
        'rolling_mean_7', 'rolling_mean_14', 'rolling_mean_30',
        'rolling_std_7', 'rolling_std_14', 'rolling_std_30',
        'ewm_7'
    ]
    
    # Drop rows with NaN in target (first few rows after lags)
    df_model = df_all_products.dropna(subset=['y']).copy()
    
    # Train / validation split (last 30 days per product as validation)
    X = df_model[feature_cols]
    y = df_model['y']
    
    # Use last 30 days of each product as validation set (by date)
    # For simplicity, we'll split by time globally
    split_date = df_model['ds'].max() - timedelta(days=30)
    train_mask = df_model['ds'] <= split_date
    val_mask = df_model['ds'] > split_date
    
    X_train, X_val = X[train_mask], X[val_mask]
    y_train, y_val = y[train_mask], y[val_mask]
    
    # LightGBM parameters
    params = {
        'objective': 'regression',
        'metric': 'rmse',
        'boosting_type': 'gbdt',
        'num_leaves': 31,
        'learning_rate': 0.05,
        'feature_fraction': 0.8,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'verbose': -1,
        'n_jobs': -1,
        'random_state': 42
    }
    
    model = lgb.LGBMRegressor(**params, n_estimators=500)
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        eval_metric='rmse',
        callbacks=[lgb.early_stopping(stopping_rounds=20, verbose=False)]
    )
    
    return model, feature_cols, le

# -------------------------------------------------------------------
# 4. Forecast next 30 days for a single product
# -------------------------------------------------------------------
def forecast_product(model, feature_cols, le, product_df, product_id):
    """
    product_df: daily dataframe for ONE product (already with features)
    Returns forecast for next 30 days (list of yhat values).
    """
    last_date = product_df['ds'].max()
    future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=30, freq='D')
    
    # Create future dataframe
    future = pd.DataFrame({'ds': future_dates})
    # Copy last known values for features that need history
    last_row = product_df.iloc[-1:].copy()
    
    # We'll iteratively predict day by day to update lags and rolling stats
    # Simpler: use last known lags and treat future as unknown (but for inventory, we can approximate)
    # For better accuracy, we'll do recursive forecasting:
    
    full_series = product_df.copy()
    for i, date in enumerate(future_dates):
        # Create row with date
        new_row = {'ds': date, 'y': np.nan, 'discount_active': 0, 'product_id': product_id}
        # Add to series temporarily for feature calculation
        temp_df = pd.concat([full_series, pd.DataFrame([new_row])], ignore_index=True)
        temp_df = add_time_features(temp_df)  # recompute features for all
        
        # Use last row features for prediction
        features_row = temp_df.iloc[-1:][feature_cols]
        # product_encoded
        features_row['product_encoded'] = le.transform([product_id])[0]
        pred = model.predict(features_row)[0]
        pred = max(0, pred)  # no negative sales
        
        # Append to full series with predicted value
        new_row['y'] = pred
        full_series = pd.concat([full_series, pd.DataFrame([new_row])], ignore_index=True)
    
    # The last 30 rows of full_series are the forecast
    forecast = full_series.tail(30)['y'].values
    return forecast

# -------------------------------------------------------------------
# 5. Restock calculation using forecast uncertainty
# -------------------------------------------------------------------
def calculate_restock_v3(forecast_30d, current_stock, lead_time_days=7, service_level_z=1.65):
    """
    Sanity-checked restock logic.
    forecast_30d: array of next 30 days predicted sales
    """
    avg_daily = np.mean(forecast_30d)
    if avg_daily <= 0:
        return {"restock_recommended": False, "restock_quantity": 0, "safety_stock": 0, "reorder_point": 0}
    
    # Days until stockout based on forecast
    cum = 0
    days_until_out = 30
    for i, sales in enumerate(forecast_30d):
        cum += sales
        if cum >= current_stock:
            days_until_out = i + 1
            break
    
    # Lead time demand
    lead_demand = avg_daily * lead_time_days
    
    # Safety stock (using forecast error – simplified here with std of first 7 days)
    forecast_std = np.std(forecast_30d[:lead_time_days]) if len(forecast_30d) >= lead_time_days else avg_daily * 0.2
    safety_stock = int(service_level_z * forecast_std * np.sqrt(lead_time_days))
    
    reorder_point = int(lead_demand + safety_stock)
    
    # RESTOCK QUANTITY: only what's needed to cover lead time + safety, NOT 30 days
    # If stockout is imminent (< lead_time), order enough to cover lead_time + buffer
    if days_until_out <= lead_time_days:
        # Emergency: order enough to cover lead time demand plus safety, minus what's left
        needed_for_lead = max(0, lead_demand + safety_stock - current_stock)
        # But also add a reasonable buffer (7 extra days)
        restock_quantity = int(needed_for_lead + (avg_daily * 7))
    else:
        # Normal: order to bring stock up to (lead_demand + safety_stock + 14 days buffer)
        target_stock = lead_demand + safety_stock + (avg_daily * 14)
        restock_quantity = max(0, int(target_stock - current_stock))
    
    # CAP: never order more than 60 days of demand
    max_order = int(avg_daily * 60)
    restock_quantity = min(restock_quantity, max_order)
    
    # Also cap by a reasonable absolute number if avg_daily is huge (e.g., >1000)
    if avg_daily > 500:
        restock_quantity = min(restock_quantity, int(avg_daily * 30))
    
    restock_recommended = (days_until_out <= lead_time_days) or (current_stock <= reorder_point)
    
    return {
        "restock_recommended": restock_recommended,
        "restock_quantity": restock_quantity,
        "safety_stock": safety_stock,
        "reorder_point": reorder_point,
        "days_until_stockout": days_until_out
    }

# -------------------------------------------------------------------
# 6. Main prediction function (replaces run_prediction)
# -------------------------------------------------------------------
# Global cache for model and encoder (train once per process)
_GLOBAL_MODEL = None
_GLOBAL_FEATURES = None
_GLOBAL_ENCODER = None
_GLOBAL_TRAINED = False

def run_prediction(sales_logs, current_stock, reorder_point):
    """
    Main entry point: expects sales_logs for a SINGLE product.
    Returns dict with predictions and restock info.
    """
    global _GLOBAL_MODEL, _GLOBAL_FEATURES, _GLOBAL_ENCODER, _GLOBAL_TRAINED
    
    if not sales_logs:
        return _empty_result()
    
    # Build daily time series
    df = build_product_ts(sales_logs, product_id='single_product')
    if len(df) < 7:
        avg = df['y'].mean()
        return _average_result(avg, current_stock, reorder_point, len(df))
    
    # Add features
    df = add_time_features(df)
    original_len = len(df)   # <-- STORE ORIGINAL LENGTH (before forecast)
    
    # Train product-specific model if enough data (>= 30 days)
    if len(df) >= 30:
        feature_cols = [c for c in df.columns if c not in ['ds', 'y', 'product_id']]
        df_model = df.dropna(subset=feature_cols + ['y']).copy()
        if len(df_model) >= 14:
            X = df_model[feature_cols]
            y = df_model['y']
            split_idx = int(len(df_model) * 0.8)
            X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
            y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]
            
            model = lgb.LGBMRegressor(n_estimators=200, max_depth=5, learning_rate=0.05, verbose=-1)
            model.fit(X_train, y_train, eval_set=[(X_val, y_val)], callbacks=[lgb.early_stopping(10, verbose=False)])
            
            # Forecast recursively
            forecast = []
            for i in range(30):
                next_date = df['ds'].max() + timedelta(days=i+1)
                new_row = {
                    'ds': next_date,
                    'y': 0,
                    'discount_active': 0,
                    'product_id': 'single_product'
                }
                temp = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                temp = add_time_features(temp)
                feat = temp.iloc[-1:][feature_cols]
                pred = model.predict(feat)[0]
                pred = max(0, pred)
                forecast.append(pred)
                new_row['y'] = pred
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                df = add_time_features(df)
            
            forecast_30d = np.array(forecast)
        else:
            avg = df['y'].mean()
            return _average_result(avg, current_stock, reorder_point, len(df))
    else:
        avg = df['y'].mean()
        return _average_result(avg, current_stock, reorder_point, len(df))
    
    # Compute aggregate predictions
    pred_7d = round(float(forecast_30d[:7].sum()), 1)
    pred_14d = round(float(forecast_30d[:14].sum()), 1)
    pred_30d = round(float(forecast_30d.sum()), 1)
    
    # Confidence based on ORIGINAL data length (not inflated by forecast rows)
    if original_len >= 180:
        confidence = 90.0
    elif original_len >= 90:
        confidence = 80.0
    elif original_len >= 30:
        confidence = 65.0
    else:
        confidence = 45.0
    
    # Restock calculation (v3, sane caps)
    restock = calculate_restock_v3(forecast_30d, current_stock)
    days_until_stockout = restock['days_until_stockout']
    restock_recommended = restock['restock_recommended']
    restock_quantity = restock['restock_quantity']
    
    return {
        "predicted_units_7d": pred_7d,
        "predicted_units_14d": pred_14d,
        "predicted_units_30d": pred_30d,
        "days_until_stockout": days_until_stockout,
        "confidence_score": confidence,
        "restock_recommended": restock_recommended,
        "restock_quantity": restock_quantity,
        "method": "lightgbm_per_product"
    }

# -------------------------------------------------------------------
# 7. Fallback helpers (same as before but kept for compatibility)
# -------------------------------------------------------------------
def _average_result(avg_daily, current_stock, reorder_point, n):
    pred_7d = round(avg_daily * 7, 1)
    pred_14d = round(avg_daily * 14, 1)
    pred_30d = round(avg_daily * 30, 1)
    days_until_stockout = round(current_stock / avg_daily, 1) if avg_daily > 0 else 999.0
    restock_recommended = days_until_stockout <= 7 or current_stock <= reorder_point
    return {
        "predicted_units_7d": pred_7d,
        "predicted_units_14d": pred_14d,
        "predicted_units_30d": pred_30d,
        "days_until_stockout": days_until_stockout,
        "confidence_score": 35.0,
        "restock_recommended": restock_recommended,
        "restock_quantity": int(pred_30d * 1.2),
        "method": "average_fallback"
    }

def _empty_result():
    return {
        "predicted_units_7d": 0,
        "predicted_units_14d": 0,
        "predicted_units_30d": 0,
        "days_until_stockout": 999,
        "confidence_score": 0,
        "restock_recommended": False,
        "restock_quantity": 0,
        "method": "no_data"
    }