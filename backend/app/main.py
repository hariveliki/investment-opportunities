"""Equity Drawdown Scanner - FastAPI Application."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import scan, detail

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Equity Drawdown Scanner",
    description="Screen equities for significant price drops over configurable horizons",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scan.router)
app.include_router(detail.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
