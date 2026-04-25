"""AzL Pools — Pool Detection Service.

Fetches aerial imagery and runs U-Net ONNX model to detect swimming pools.
Consumes from Redis queue, stores results in PostgreSQL.
"""

import os
import io
import logging
from contextlib import asynccontextmanager

import numpy as np
import onnxruntime as ort
from fastapi import FastAPI, HTTPException
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from imagery.fetcher import fetch_aerial_image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://poolprospect:localdev@localhost:5432/poolprospect")
MODEL_PATH = os.getenv("MODEL_PATH", "models/pool_detector.onnx")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
DETECTION_THRESHOLD = float(os.getenv("DETECTION_THRESHOLD", "0.5"))

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Load ONNX model with CPU-only execution
ort_session = None


def load_model():
    global ort_session
    if os.path.exists(MODEL_PATH):
        ort_session = ort.InferenceSession(MODEL_PATH, providers=["CPUExecutionProvider"])
        logger.info(f"Loaded ONNX model from {MODEL_PATH}")
    else:
        logger.warning(f"Model not found at {MODEL_PATH} — detection will return dummy results")


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_model()
    yield


app = FastAPI(title="AzL Pools — Pool Detection", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": ort_session is not None}


@app.post("/detect/{property_id}")
async def detect_pool(property_id: int):
    """Fetch aerial image for a property and run pool detection."""
    with SessionLocal() as session:
        row = session.execute(
            "SELECT latitude, longitude, parcel_id FROM properties WHERE id = :id",
            {"id": property_id},
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Property not found")

    lat, lon, parcel_id = float(row[0]), float(row[1]), row[2]

    # Fetch aerial image
    try:
        img_bytes = await fetch_aerial_image(lat, lon)
    except Exception as e:
        logger.error(f"Failed to fetch imagery for property {property_id}: {e}")
        raise HTTPException(status_code=502, detail="Imagery fetch failed")

    # Run inference
    score, has_pool = run_detection(img_bytes)

    # Store result
    with SessionLocal() as session:
        session.execute(
            "INSERT INTO pool_analysis (property_id, detection_score, has_pool, analyzed_at) "
            "VALUES (:pid, :score, :has_pool, NOW())",
            {"pid": property_id, "score": score, "has_pool": has_pool},
        )
        session.execute(
            "UPDATE properties SET pool_detected = :detected WHERE id = :id",
            {"detected": has_pool, "id": property_id},
        )
        session.commit()

    logger.info(f"Property {property_id} ({parcel_id}): pool={'YES' if has_pool else 'NO'} score={score:.4f}")
    return {"property_id": property_id, "has_pool": has_pool, "score": round(score, 4)}


def run_detection(img_bytes: bytes) -> tuple[float, bool]:
    """Run U-Net ONNX inference on an aerial image."""
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB").resize((256, 256))
    img_array = np.array(img, dtype=np.float32) / 255.0
    img_array = np.transpose(img_array, (2, 0, 1))  # HWC → CHW
    img_array = np.expand_dims(img_array, 0)  # Add batch dim → NCHW

    if ort_session is None:
        # Dummy result when model not loaded
        return 0.0, False

    outputs = ort_session.run(None, {ort_session.get_inputs()[0].name: img_array})
    mask = outputs[0]
    score = float(mask.max())
    has_pool = score > DETECTION_THRESHOLD
    return score, has_pool


@app.post("/batch-detect")
async def batch_detect(property_ids: list[int]):
    """Detect pools for a batch of property IDs."""
    results = []
    for pid in property_ids:
        try:
            result = await detect_pool(pid)
            results.append(result)
        except HTTPException as e:
            results.append({"property_id": pid, "error": e.detail})
    return {"results": results, "total": len(results)}
