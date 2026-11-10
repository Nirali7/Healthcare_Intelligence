"""Data cleaning, KPIs and text insights."""
import pandas as pd
import numpy as np

DATE_COLUMNS = ["admission_date", "discharge_date"]
NUMERIC_COLUMNS = ["age", "billing_amount", "room_number"]


def prepare_analytics_data(data):
    if data is None:
        return pd.DataFrame()
    df = data.copy()
    if df.empty:
        return df
    df.columns = [str(c).lower().strip() for c in df.columns]

    for col in DATE_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "admission_date" in df.columns and "discharge_date" in df.columns:
        stay = (df["discharge_date"] - df["admission_date"]).dt.days
        df["length_of_stay"] = stay.clip(lower=0)
    else:
        df["length_of_stay"] = np.nan

    if "billing_amount" in df.columns:
        df["billing_amount"] = pd.to_numeric(df["billing_amount"], errors="coerce")
    if "age" in df.columns:
        df["age"] = pd.to_numeric(df["age"], errors="coerce")
    return df


def calculate_kpis(data):
    df = data if data is not None else pd.DataFrame()
    if df.empty:
        return {"total_patients": 0, "average_age": 0, "average_billing": 0, "average_stay": 0}
    return {
        "total_patients": int(len(df)),
        "average_age": float(df["age"].mean()) if "age" in df.columns and df["age"].notna().any() else 0,
        "average_billing": float(df["billing_amount"].mean()) if "billing_amount" in df.columns and df["billing_amount"].notna().any() else 0,
        "average_stay": float(df["length_of_stay"].mean()) if "length_of_stay" in df.columns and df["length_of_stay"].notna().any() else 0,
    }


def get_top_category(data, column):
    if data is None or data.empty or column not in data.columns:
        return "Not available"
    counts = data[column].dropna().astype(str).value_counts()
    return str(counts.index[0]) if not counts.empty else "Not available"


def generate_insights(data):
    if data is None or data.empty:
        return ["No records match the selected filters. Try selecting more inclusive filters."]
    insights = [f"Showing **{len(data):,}** patient records for the current filter selection."]
    for col, label in [
        ("medical_condition", "most common medical condition"),
        ("hospital", "hospital with the most records"),
        ("insurance_provider", "most common insurance provider"),
        ("admission_type", "most common admission type"),
    ]:
        top = get_top_category(data, col)
        if top != "Not available":
            insights.append(f"The {label} is **{top}**.")
    if "billing_amount" in data.columns and data["billing_amount"].notna().any():
        insights.append(f"Average billing amount is **{data['billing_amount'].mean():,.2f}**.")
    if "length_of_stay" in data.columns and data["length_of_stay"].notna().any():
        insights.append(f"Average length of stay is **{data['length_of_stay'].mean():.1f} days**.")
    return insights


def get_summary_statistics(data):
    if data is None or data.empty:
        return {"records": 0, "columns": 0, "missing_cells": 0}
    return {
        "records": int(len(data)),
        "columns": int(len(data.columns)),
        "missing_cells": int(data.isna().sum().sum()),
    }
