"""FastAPI entry point — replaces CICS region startup."""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .api import router
from .database import init_db
from .config import DB_PATH, COMPANY_NAME

app = FastAPI(title=COMPANY_NAME, version="1.0.0")
app.include_router(router)

_static_dir = Path(__file__).resolve().parent.parent.parent / "static"
if _static_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(_static_dir), html=True), name="static")


@app.on_event("startup")
def startup():
    init_db(DB_PATH)
