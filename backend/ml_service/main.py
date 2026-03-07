"""
ML Sub-Service (v1.0)
---------------------
Lightweight FastAPI application for ML inference tasks.

Run independently on port 8001:
    uvicorn ml_service.main:app --port 8001 --reload

The main application (port 8000) calls this service internally via httpx:
    POST http://localhost:8001/predict/questions
    POST http://localhost:8001/predict/performance

This service is OPTIONAL in Phase 1. The Interview module works without it
using the built-in question bank in InterviewService.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ml_service.routers import predict

app = FastAPI(
    title="ML Service",
    description="Lightweight ML inference service for interview question generation and performance prediction.",
    version="1.0.0",
)

# Allow calls from the main app only (internal)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],
    allow_credentials=False,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

app.include_router(predict.router, prefix="/predict", tags=["Predictions"])


@app.get("/", tags=["Root"])
async def root():
    return {"service": "ml_service", "version": "1.0.0", "status": "ok"}
