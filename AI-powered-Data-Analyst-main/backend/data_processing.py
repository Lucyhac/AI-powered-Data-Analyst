import io
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def load_dataset(file_buffer: bytes, filename: str) -> pd.DataFrame:
    """Load CSV or Excel content from uploaded bytes into a DataFrame."""
    logger.info("Loading dataset: %s", filename)
    ext = filename.lower().split(".")[-1]
    try:
        if ext in {"csv", "txt"}:
            df = pd.read_csv(io.BytesIO(file_buffer))
        elif ext in {"xls", "xlsx"}:
            df = pd.read_excel(io.BytesIO(file_buffer))
        else:
            raise ValueError("Unsupported file type. Please upload CSV or Excel.")
    except Exception as exc:  # pragma: no cover - surfaced to UI
        logger.exception("Failed to load dataset %s", filename)
        raise ValueError(f"Unable to read file {filename}: {exc}")

    if df.empty:
        raise ValueError(f"The file {filename} appears to be empty.")

    return df


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names to snake_case."""
    df = df.copy()
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.replace(r"[^0-9a-zA-Z]+", "_", regex=True)
        .str.lower()
    )
    return df


def convert_dates(df: pd.DataFrame, max_unique: int = 200) -> pd.DataFrame:
    """Attempt to parse object columns to datetime when cardinality is reasonable."""
    df = df.copy()
    for col in df.columns:
        if df[col].dtype == object and df[col].nunique(dropna=True) <= max_unique:
            try:
                parsed = pd.to_datetime(df[col], errors="raise", infer_datetime_format=True)
                df[col] = parsed
                logger.info("Column %s converted to datetime", col)
            except Exception:
                continue
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Deduplicate, drop fully empty columns/rows, and standardize types."""
    df = df.copy()
    before = len(df)
    df.drop_duplicates(inplace=True)
    logger.info("Dropped %s duplicate rows", before - len(df))

    df.dropna(how="all", inplace=True)
    df.dropna(axis=1, how="all", inplace=True)

    df = normalize_columns(df)
    df = convert_dates(df)

    # handle missing values: numeric mean, categorical mode
    for col in df.columns:
        if df[col].isnull().any():
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col].fillna(df[col].mean(), inplace=True)
            else:
                mode = df[col].mode(dropna=True)
                if not mode.empty:
                    df[col].fillna(mode.iloc[0], inplace=True)
                else:
                    df[col].fillna("missing", inplace=True)
    return df.reset_index(drop=True)


def detect_types(df: pd.DataFrame) -> Tuple[List[str], List[str]]:
    """Return lists of numeric and categorical columns."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = [
        col for col in df.columns if col not in numeric_cols and df[col].nunique() <= 50
    ]
    return numeric_cols, categorical_cols


def basic_summary(df: pd.DataFrame, numeric_cols: List[str]) -> pd.DataFrame:
    if not numeric_cols:
        return pd.DataFrame()
    summary = df[numeric_cols].describe().T
    summary["missing"] = df[numeric_cols].isnull().sum()
    return summary.reset_index().rename(columns={"index": "column"})


def grouped_analysis(df: pd.DataFrame, group_col: Optional[str], numeric_cols: List[str]) -> pd.DataFrame:
    if not group_col or group_col not in df.columns or not numeric_cols:
        return pd.DataFrame()
    grouped = df.groupby(group_col)[numeric_cols].agg(["count", "sum", "mean"])
    # flatten MultiIndex columns
    grouped.columns = ["_".join(col).rstrip("_") for col in grouped.columns.values]
    grouped = grouped.reset_index()
    return grouped


def generate_insights(df: pd.DataFrame, numeric_cols: List[str]) -> List[str]:
    insights = []
    if not numeric_cols:
        return ["No numeric columns detected; showing data preview only."]
    for col in numeric_cols:
        series = df[col].dropna()
        if series.empty:
            continue
        insights.append(f"{col}: mean={series.mean():.2f}, median={series.median():.2f}, max={series.max():.2f}")
    return insights or ["No insights could be computed."]


def merge_datasets(datasets: List[pd.DataFrame]) -> pd.DataFrame:
    """Concatenate multiple cleaned datasets."""
    if not datasets:
        raise ValueError("No datasets provided")
    return pd.concat(datasets, ignore_index=True, sort=False)


def compute_kpis(df: pd.DataFrame, numeric_cols: List[str], categorical_cols: List[str]) -> Dict:
    total_rows = len(df)
    total_cols = len(df.columns)
    missing_count = int(df.isnull().sum().sum())
    missing_pct = float(missing_count) / float(df.size) * 100 if df.size else 0.0
    duplicates = df.duplicated().sum()
    return {
        "rows": total_rows,
        "columns": total_cols,
        "numeric_columns": len(numeric_cols),
        "categorical_columns": len(categorical_cols),
        "missing_percent": round(missing_pct, 2),
        "missing_count": missing_count,
        "duplicates": int(duplicates),
    }


def pipeline(files: List[Tuple[bytes, str]], group_col: Optional[str] = None) -> Dict:
    """Full processing pipeline returning cleaned data, summary, grouped stats, insights, KPIs."""
    cleaned_frames: List[pd.DataFrame] = []
    for buffer, name in files:
        raw = load_dataset(buffer, name)
        cleaned_frames.append(clean_data(raw))

    combined = merge_datasets(cleaned_frames) if len(cleaned_frames) > 1 else cleaned_frames[0]
    numeric_cols, categorical_cols = detect_types(combined)
    summary = basic_summary(combined, numeric_cols)
    grouped = grouped_analysis(combined, group_col, numeric_cols)
    insights = generate_insights(combined, numeric_cols)
    kpis = compute_kpis(combined, numeric_cols, categorical_cols)
    corr_matrix = combined[numeric_cols].corr().round(2).fillna(0).to_dict() if numeric_cols else {}
    datetime_cols = combined.select_dtypes(include=["datetime64[ns]"]).columns.tolist()

    return {
        "data": combined,
        "numeric_cols": numeric_cols,
        "categorical_cols": categorical_cols,
        "summary": summary,
        "grouped": grouped,
        "insights": insights,
        "kpis": kpis,
        "corr_matrix": corr_matrix,
        "columns": combined.columns.tolist(),
        "datetime_cols": datetime_cols,
    }


def column_profile(df: pd.DataFrame, column: str) -> Dict:
    if column not in df.columns:
        raise ValueError("Column not found")
    series = df[column]
    unique_values = series.nunique(dropna=False)
    top_freq = series.value_counts(dropna=False).head(5)
    distribution = [{"value": str(idx), "count": int(val)} for idx, val in top_freq.items()]
    return {
        "unique_values": int(unique_values),
        "top_values": distribution,
    }
