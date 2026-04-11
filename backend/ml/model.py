import pandas as pd
import numpy as np
from prophet import Prophet
import logging
logging.getLogger("prophet").setLevel(logging.WARNING)
logging.getLogger("cmdstanpy").setLevel(logging.WARNING)

def run_prediction(sales_logs: list, current_stock: int, reorder_point: int):
    if not sales_logs:
        return _empty_result()

    df = pd.DataFrame([{
        "ds": pd.to_datetime(log.date),
        "y": float(log.units_sold)
    } for log in sales_logs])

    df = df.sort_values("ds").reset_index(drop=True)
    df = df[df["y"] >= 0]

    n = len(df)
    avg_daily = float(df["y"].mean())
    max_daily = float(df["y"].max())

    # not enough data — use simple average
    if n < 14:
        return _average_result(avg_daily, current_stock, reorder_point, n)

    try:
        model = Prophet(
            yearly_seasonality=n >= 180,
            weekly_seasonality=n >= 14,
            daily_seasonality=False,
            seasonality_mode="additive",
            interval_width=0.80,
            changepoint_prior_scale=0.05
        )
        model.fit(df)

        future = model.make_future_dataframe(periods=30)
        forecast = model.predict(future)
        future_fc = forecast.tail(30).reset_index(drop=True)

        # sanity cap — never predict more than 3x historical max per day
        cap = max_daily * 3
        future_fc["yhat"] = future_fc["yhat"].clip(lower=0, upper=cap)

        pred_7d = round(float(future_fc.head(7)["yhat"].sum()), 1)
        pred_14d = round(float(future_fc.head(14)["yhat"].sum()), 1)
        pred_30d = round(float(future_fc["yhat"].sum()), 1)

        # days until stockout
        cumulative = 0.0
        days_until_stockout = 30.0
        for i, row in future_fc.iterrows():
            cumulative += max(0, row["yhat"])
            if cumulative >= current_stock:
                days_until_stockout = float(i + 1)
                break

        restock_recommended = days_until_stockout <= 7 or current_stock <= reorder_point
        restock_quantity = int(pred_30d * 1.2)

        if n >= 180:
            confidence = 90.0
        elif n >= 90:
            confidence = 78.0
        elif n >= 30:
            confidence = 65.0
        else:
            confidence = 50.0

        return {
            "predicted_units_7d": pred_7d,
            "predicted_units_14d": pred_14d,
            "predicted_units_30d": pred_30d,
            "days_until_stockout": days_until_stockout,
            "confidence_score": confidence,
            "restock_recommended": restock_recommended,
            "restock_quantity": restock_quantity,
            "method": "prophet"
        }

    except Exception as e:
        return _average_result(avg_daily, current_stock, reorder_point, n)


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