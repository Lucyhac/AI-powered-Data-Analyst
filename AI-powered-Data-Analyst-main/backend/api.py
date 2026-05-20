import io
import logging
from typing import Optional

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

from backend.data_processing import column_profile, pipeline
from backend.reporting import create_charts, generate_excel_report
from utils.logger import setup_logger

setup_logger()
logger = logging.getLogger(__name__)

app = FastAPI(title="Automated Data Analysis API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

        # build lightweight preview
        preview = results["data"].head(200).to_dict(orient="records")

        response = {
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
        return response
    except Exception as exc:  # pragma: no cover
        logger.exception("Analysis failed")
        return JSONResponse(status_code=400, content={"error": str(exc)})


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
        report_path = generate_excel_report(
            results["data"],
            results["summary"],
            results["grouped"],
            charts,
            group_col,
        )
        return FileResponse(report_path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=report_path.name)
    except Exception as exc:  # pragma: no cover
        logger.exception("Report generation failed")
        return JSONResponse(status_code=400, content={"error": str(exc)})


@app.post("/clean")
async def clean(files: list[UploadFile] = File(...), group_col: Optional[str] = Form(default=None)):
    """Return cleaned data preview and kpis."""
    if not files:
        return JSONResponse(status_code=400, content={"error": "No files uploaded"})
    buffers = []
    for f in files:
        content = await f.read()
        buffers.append((content, f.filename))
    results = pipeline(buffers, group_col=group_col)
    preview = results["data"].head(200).to_dict(orient="records")
    return {
        "preview": preview,
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
    profile = column_profile(results["data"], column)
    return profile


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
    numeric_cols = results["numeric_cols"]
    summary = results["summary"]
    insights_list = []
    recs = []
    if numeric_cols and not summary.empty:
        top_mean = summary.sort_values(by="mean", ascending=False).iloc[0]
        insights_list.append(f"'{top_mean['column']}' has the highest mean at {top_mean['mean']:.2f}.")
        recs.append(f"Monitor '{top_mean['column']}' closely; it drives magnitude of numeric performance.")
    if k.get("missing_count", 0) > 0:
        insights_list.append(f"{k['missing_count']} missing values were filled during cleaning.")
        recs.append("Review upstream data collection to reduce missing fields.")
    if k.get("duplicates", 0) > 0:
        insights_list.append(f"{k['duplicates']} duplicate rows were removed.")
        recs.append("Add unique constraints/ids to prevent duplicate ingests.")
    if not insights_list:
        insights_list.append("Data looks consistent with minimal missing or duplicate entries.")
        recs.append("Set data quality monitors to maintain current health.")
    return {"insights": insights_list[:3], "recommendations": recs[:2]}


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
    return StreamingResponse(io.BytesIO(csv_bytes), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=cleaned_data.csv"})
