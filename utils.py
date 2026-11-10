"""Small UI/data helpers."""
import pandas as pd


def format_number(value):
    try:
        return f"{float(value):,.0f}"
    except (TypeError, ValueError):
        return "0"


def format_currency(value):
    try:
        return f"₹{float(value):,.2f}"
    except (TypeError, ValueError):
        return "₹0.00"


def safe_mean(series):
    return float(series.mean()) if series is not None and series.notna().any() else 0.0


def get_filter_options(data, column):
    if data is None or data.empty or column not in data.columns:
        return []
    return sorted(data[column].dropna().astype(str).unique().tolist(), key=str.casefold)


def prepare_patient_table(data):
    if data is None:
        return pd.DataFrame()
    df = data.copy()
    preferred = [
        "patient_id", "name", "age", "gender", "hospital", "medical_condition",
        "admission_type", "insurance_provider", "admission_date", "discharge_date",
        "length_of_stay", "billing_amount", "blood_type", "doctor", "medication",
        "test_results",
    ]
    columns = [c for c in preferred if c in df.columns]
    return df[columns] if columns else df


def dataframe_to_csv(data):
    return data.to_csv(index=False).encode("utf-8-sig")


def validate_date_range(start_date, end_date):
    return start_date <= end_date
