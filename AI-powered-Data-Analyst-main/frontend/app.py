import io
import logging
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd
import streamlit as st

from backend.data_processing import pipeline
from backend.reporting import create_charts, generate_excel_report
from utils.logger import setup_logger

# Initialize logging
setup_logger()
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Automated Data Analysis & Excel Report",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Automated Data Analysis & Excel Report")
st.write("Upload CSV/XLSX files, explore the data, and download a ready-to-share Excel report.")


def _process_files(uploaded_files, group_col: Optional[str]):
    files: List[Tuple[bytes, str]] = []
    for f in uploaded_files:
        f.seek(0)
        files.append((f.read(), f.name))
    return pipeline(files, group_col=group_col)


def _filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Lightweight row filter based on a selected column/value."""
    filter_col = st.selectbox("Optional filter column", ["-- none --"] + df.columns.tolist(), index=0)
    if filter_col != "-- none --":
        unique_vals = df[filter_col].dropna().unique().tolist()
        if unique_vals:
            chosen = st.multiselect("Select values to include", unique_vals)
            if chosen:
                return df[df[filter_col].isin(chosen)]
    return df


with st.sidebar:
    st.header("Upload")
    uploaded_files = st.file_uploader(
        "Upload one or more CSV/XLSX files",
        type=["csv", "xlsx", "xls"],
        accept_multiple_files=True,
    )
    st.markdown("Tip: You can drag multiple files at once.")

placeholder_status = st.empty()

if uploaded_files:
    st.success(f"{len(uploaded_files)} file(s) uploaded.")
    try:
        # Infer default group column after loading
        placeholder_status.info("Processing files...")
        with st.spinner("Cleaning and analyzing data..."):
            first_file = uploaded_files[0].name
            group_selection_holder = st.empty()
            # Preload once to identify possible group columns
            uploaded_files[0].seek(0)
            temp_df = (
                pd.read_csv(uploaded_files[0])
                if first_file.lower().endswith(".csv")
                else pd.read_excel(uploaded_files[0])
            )
            uploaded_files[0].seek(0)
            temp_df = temp_df.reset_index(drop=True)
            group_options = ["-- none --"] + temp_df.columns.tolist()
            group_col_choice = group_selection_holder.selectbox(
                "Choose optional grouping column (applied after cleaning)",
                group_options,
                index=0,
            )
            group_col = None if group_col_choice == "-- none --" else group_col_choice

            results = _process_files(uploaded_files, group_col)

        cleaned_df = results["data"]
        numeric_cols = results["numeric_cols"]
        summary_df = results["summary"]
        grouped_df = results["grouped"]
        insights = results["insights"]
        categorical_cols = results["categorical_cols"]

        placeholder_status.success("Processing complete.")

        st.subheader("Data Preview")
        st.dataframe(cleaned_df.head(200))

        st.subheader("Summary Metrics")
        if not summary_df.empty:
            st.dataframe(summary_df)
        else:
            st.info("No numeric columns detected for summary statistics.")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Key Insights")
            st.write("\n".join([f"• {i}" for i in insights]))
        with col2:
            st.subheader("Columns")
            st.write(f"Numeric: {numeric_cols if numeric_cols else 'None'}")
            st.write(f"Categorical (<=50 unique): {categorical_cols if categorical_cols else 'None'}")

        st.subheader("Grouped Analysis")
        if not grouped_df.empty:
            st.dataframe(grouped_df)
        else:
            st.info("Select a grouping column to see aggregated metrics.")

        st.subheader("Charts")
        chart_col = st.selectbox(
            "Chart grouping column",
            ["-- auto --"] + categorical_cols,
            index=0,
            help="Select a categorical column to group charts. Default uses the first categorical column.",
        )
        chosen_group = None if chart_col == "-- auto --" else chart_col
        chosen_group = chosen_group or (categorical_cols[0] if categorical_cols else None)

        charts = create_charts(cleaned_df, chosen_group, numeric_cols)
        if charts:
            for title, path in charts:
                st.image(path, caption=title, use_column_width=True)
        else:
            st.info("Upload numeric data to view charts.")

        st.subheader("Filter & Explore")
        filtered_df = _filter_dataframe(cleaned_df)
        st.dataframe(filtered_df.head(200))

        if st.button("Generate Excel Report", type="primary"):
            with st.spinner("Building Excel report..."):
                report_path = generate_excel_report(cleaned_df, summary_df, grouped_df, charts, chosen_group)
            with open(report_path, "rb") as f:
                st.download_button(
                    label="Download Excel Report",
                    data=f,
                    file_name=Path(report_path).name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
                st.success(f"Report ready: {Path(report_path).name}")

    except Exception as exc:  # pragma: no cover - surfaced to UI
        logger.exception("Processing failed")
        st.error(f"Error: {exc}")
else:
    st.info("Upload CSV/XLSX files from the sidebar to get started.")
