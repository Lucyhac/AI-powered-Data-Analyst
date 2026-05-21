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
