import matplotlib
matplotlib.use("Agg")

import io
import logging
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import (
    FileResponse,
    JSONResponse,
    StreamingResponse,
)

from backend.data_processing import pipeline, column_profile
from backend.reporting import (
    create_charts,
    generate_excel_report,
)
from utils.logger import setup_logger

setup_logger()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Powered Data Analyst API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "AI Powered Data Analyst API Running"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/analyze")
async def analyze(
    files: list[UploadFile] = File(...),
    group_col: Optional[str] = Form(default=None),
):
    if not files:
        return JSONResponse(status_code=400, content={"error": "No files uploaded"})
    try:
        buffers = []
        for f in files:
            content = await f.read()
            buffers.append((content, f.filename))
        results = pipeline(buffers, group_col=group_col)
        charts = create_charts(results["data"], group_col, results["numeric_cols"])
        preview = results["data"].head(200).to_dict(orient="records")
        return {
            "preview": preview,
            "columns": results["columns"],
            "datetime_cols": results["datetime_cols"],
            "numeric_cols": results["numeric_cols"],
            "categorical_cols": results["categorical_cols"],
            "summary": results["summary"].to_dict(orient="records"),
            "grouped": results["grouped"].to_dict(orient="records"),
            "insights": results["insights"],
            "charts": charts,
            "kpis": results.get("kpis", {}),
            "corr_matrix": results.get("corr_matrix", {}),
        }
    except Exception as exc:
        logger.exception("Analysis failed")
        return JSONResponse(status_code=500, content={"error": str(exc)})

@app.post("/report")
async def report(
    files: list[UploadFile] = File(...),
    group_col: Optional[str] = Form(default=None),
):
    if not files:
        return JSONResponse(status_code=400, content={"error": "No files uploaded"})
    try:
        buffers = []
        for f in files:
            content = await f.read()
            buffers.append((content, f.filename))
        results = pipeline(buffers, group_col=group_col)
        charts = create_charts(results["data"], group_col, results["numeric_cols"])
        report_path = generate_excel_report(results["data"], results["summary"], results["grouped"], charts, group_col)
        return FileResponse(
            report_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=report_path.name,
        )
    except Exception as exc:
        logger.exception("Report generation failed")
        return JSONResponse(status_code=500, content={"error": str(exc)})

@app.post("/clean")
async def clean(
    files: list[UploadFile] = File(...),
    group_col: Optional[str] = Form(default=None),
):
    if not files:
        return JSONResponse(status_code=400, content={"error": "No files uploaded"})
    buffers = []
    for f in files:
        content = await f.read()
        buffers.append((content, f.filename))
    results = pipeline(buffers, group_col=group_col)
    return {
        "preview": results["data"].head(200).to_dict(orient="records"),
        "kpis": results["kpis"],
        "columns": results["columns"],
        "numeric_cols": results["numeric_cols"],
        "categorical_cols": results["categorical_cols"],
        "datetime_cols": results["datetime_cols"],
    }

@app.post("/column-stats")
async def column_stats(
    column: str = Form(...),
    files: list[UploadFile] = File(...),
):
    if not files:
        return JSONResponse(status_code=400, content={"error": "No files uploaded"})
    buffers = []
    for f in files:
        content = await f.read()
        buffers.append((content, f.filename))
    results = pipeline(buffers)
    return column_profile(results["data"], column)

@app.post("/insights")
async def insights(files: list[UploadFile] = File(...)):
    if not files:
        return JSONResponse(status_code=400, content={"error": "No files uploaded"})
    buffers = []
    for f in files:
        content = await f.read()
        buffers.append((content, f.filename))
    results = pipeline(buffers)
    k = results["kpis"]
    summary = results["summary"]
    numeric_cols = results["numeric_cols"]
    insights_list = []
    recommendations = []
    if numeric_cols and not summary.empty:
        top_mean = summary.sort_values(by="mean", ascending=False).iloc[0]
        insights_list.append(f"{top_mean['column']} has highest average value at {top_mean['mean']:.2f}")
        recommendations.append(f"Focus on optimizing {top_mean['column']} for better performance.")
    if k.get("missing_count", 0) > 0:
        insights_list.append(f"{k['missing_count']} missing values detected and cleaned.")
        recommendations.append("Improve upstream data quality collection.")
    if k.get("duplicates", 0) > 0:
        insights_list.append(f"{k['duplicates']} duplicate rows removed.")
        recommendations.append("Add unique identifiers to prevent duplicates.")
    if not insights_list:
        insights_list.append("Dataset quality is excellent with minimal inconsistencies.")
        recommendations.append("Maintain current data governance standards.")
    return {"insights": insights_list[:5], "recommendations": recommendations[:5]}

@app.post("/download-clean")
async def download_clean(files: list[UploadFile] = File(...)):
    if not files:
        return JSONResponse(status_code=400, content={"error": "No files uploaded"})
    buffers = []
    for f in files:
        content = await f.read()
        buffers.append((content, f.filename))
    results = pipeline(buffers)
    csv_bytes = results["data"].to_csv(index=False).encode("utf-8")
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=cleaned_data.csv"},
    )

# Required by Vercel
handler = app
