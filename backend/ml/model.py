import pandas as pd
import numpy as np
from prophet import Prophet
import logging
logging.getLogger("prophet").setLevel(logging.WARNING)
logging.getLogger("cmdstanpy").setLevel(logging.WARNING)

def get_indian_holidays():
    years = [2022, 2023, 2024, 2025, 2026]
    holidays = []

    fixed = [
        ("New Year", "01-01"),
        ("Republic Day", "01-26"),
        ("Independence Day", "08-15"),
        ("Gandhi Jayanti", "10-02"),
        ("Christmas", "12-25"),
    ]

    for year in years:
        for name, date in fixed:
            holidays.append({"holiday": name, "ds": pd.Timestamp(f"{year}-{date}"), "lower_window": -1, "upper_window": 1})

    # Approximate floating holidays (common dates vary by year slightly)
    floating = [
        ("Diwali", ["2022-10-24", "2023-11-12", "2024-11-01", "2025-10-20", "2026-11-08"]),
        ("Holi", ["2022-03-18", "2023-03-08", "2024-03-25", "2025-03-14", "2026-03-03"]),
        ("Dussehra", ["2022-10-05", "2023-10-24", "2024-10-12", "2025-10-02", "2026-10-20"]),
        ("Eid ul Fitr", ["2022-05-03", "2023-04-22", "2024-04-10", "2025-03-31", "2026-03-20"]),
        ("Eid ul Adha", ["2022-07-10", "2023-06-29", "2024-06-17", "2025-06-07", "2026-05-27"]),
        ("Navratri", ["2022-10-02", "2023-10-15", "2024-10-03", "2025-09-22", "2026-10-11"]),
        ("Raksha Bandhan", ["2022-08-11", "2023-08-30", "2024-08-19", "2025-08-09", "2026-07-29"]),
        ("Durga Puja", ["2022-10-02", "2023-10-21", "2024-10-09", "2025-09-29", "2026-10-18"]),
    ]

    for name, dates in floating:
        for d in dates:
            holidays.append({"holiday": name, "ds": pd.Timestamp(d), "lower_window": -2, "upper_window": 3})

    return pd.DataFrame(holidays)


def get_month_markers(df):
    """Add month-end and month-start spikes as regressors"""
    df = df.copy()
    df["month_end"] = df["ds"].apply(lambda x: 1 if x.day >= 28 else 0)
    df["month_start"] = df["ds"].apply(lambda x: 1 if x.day <= 2 else 0)
    df["is_weekend"] = df["ds"].apply(lambda x: 1 if x.dayofweek >= 5 else 0)
    df["indian_season"] = df["ds"].apply(get_indian_season)
    return df


def get_indian_season(date):
    month = date.month
    if month in [3, 4, 5]:
        return 2  # Summer
    elif month in [6, 7, 8, 9]:
        return 3  # Monsoon
    elif month in [10, 11]:
        return 1  # Festive/Autumn
    else:
        return 0  # Winter


def make_future_regressors(future_df):
    future_df = future_df.copy()
    future_df["month_end"] = future_df["ds"].apply(lambda x: 1 if x.day >= 28 else 0)
    future_df["month_start"] = future_df["ds"].apply(lambda x: 1 if x.day <= 2 else 0)
    future_df["is_weekend"] = future_df["ds"].apply(lambda x: 1 if x.dayofweek >= 5 else 0)
    future_df["indian_season"] = future_df["ds"].apply(get_indian_season)
    future_df["discount_active"] = 0
    return future_df


def run_prediction(sales_logs: list, current_stock: int, reorder_point: int):
    if not sales_logs:
        return _empty_result()

    df = pd.DataFrame([{
        "ds": pd.to_datetime(log.date),
        "y": float(log.units_sold),
        "discount_active": float(getattr(log, "discount_active", 0) or 0)
    } for log in sales_logs])

    df = df.sort_values("ds").reset_index(drop=True)
    df = df[df["y"] >= 0]

    n = len(df)
    avg_daily = float(df["y"].mean())
    max_daily = float(df["y"].max())

    if n < 14:
        return _average_result(avg_daily, current_stock, reorder_point, n)

    try:
        df = get_month_markers(df)
        holidays = get_indian_holidays()

        model = Prophet(
            yearly_seasonality=n >= 180,
            weekly_seasonality=n >= 14,
            daily_seasonality=False,
            seasonality_mode="multiplicative",
            interval_width=0.80,
            changepoint_prior_scale=0.05,
            holidays=holidays,
            holidays_prior_scale=10.0,
        )

        model.add_regressor("month_end", prior_scale=5.0)
        model.add_regressor("month_start", prior_scale=5.0)
        model.add_regressor("is_weekend", prior_scale=3.0)
        model.add_regressor("indian_season", prior_scale=3.0)
        model.add_regressor("discount_active", prior_scale=8.0)

        model.fit(df[["ds", "y", "month_end", "month_start", "is_weekend", "indian_season", "discount_active"]])

        future = model.make_future_dataframe(periods=30)
        future = make_future_regressors(future)

        forecast = model.predict(future)
        future_fc = forecast.tail(30).reset_index(drop=True)

        # sanity cap — never more than 3x historical max per day
        cap = max_daily * 3
        future_fc["yhat"] = future_fc["yhat"].clip(lower=0, upper=cap)

        pred_7d = round(float(future_fc.head(7)["yhat"].sum()), 1)
        pred_14d = round(float(future_fc.head(14)["yhat"].sum()), 1)
        pred_30d = round(float(future_fc["yhat"].sum()), 1)

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
            confidence = 92.0
        elif n >= 90:
            confidence = 80.0
        elif n >= 30:
            confidence = 67.0
        else:
            confidence = 52.0

        return {
            "predicted_units_7d": pred_7d,
            "predicted_units_14d": pred_14d,
            "predicted_units_30d": pred_30d,
            "days_until_stockout": days_until_stockout,
            "confidence_score": confidence,
            "restock_recommended": restock_recommended,
            "restock_quantity": restock_quantity,
            "method": "prophet_v2"
        }

    except Exception as e:
        print(f"Prophet error: {e}")
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