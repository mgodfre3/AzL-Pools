"""Pool detection activity — fetches aerial imagery and runs U-Net ONNX model."""

import io
import logging
import os

import numpy as np
import onnxruntime as ort
from PIL import Image
import azure.durable_functions as df
from sqlalchemy import text

from shared.config import BING_MAPS_KEY, DETECTION_THRESHOLD
from shared.db import SessionLocal

logger = logging.getLogger(__name__)
bp = df.Blueprint()

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "pool_detector.onnx")
_ort_session = None


def _get_session():
    global _ort_session
    if _ort_session is None and os.path.exists(MODEL_PATH):
        _ort_session = ort.InferenceSession(MODEL_PATH, providers=["CPUExecutionProvider"])
        logger.info("Loaded pool detection ONNX model")
    return _ort_session


@bp.activity_trigger(input_name="input")
async def detect_pool_activity(input: dict) -> dict:
    """Fetch aerial image for a property and run pool detection."""
    property_id = input["property_id"]

    with SessionLocal() as session:
        row = session.execute(
            text("SELECT latitude, longitude FROM properties WHERE id = :id"),
            {"id": property_id},
        ).fetchone()

    if not row or not row[0] or not row[1]:
        return {"property_id": property_id, "has_pool": None, "score": 0, "error": "no coordinates"}

    lat, lon = float(row[0]), float(row[1])

    # Fetch aerial image
    import httpx
    url = (
        f"https://dev.virtualearth.net/REST/v1/Imagery/Map/Aerial/"
        f"{lat},{lon}/20?mapSize=500,500&key={BING_MAPS_KEY}"
    )
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        img_bytes = resp.content

    # Run detection
    score, has_pool = _run_inference(img_bytes)

    # Store result
    with SessionLocal() as session:
        session.execute(text(
            "INSERT INTO pool_analysis (property_id, detection_score, has_pool, analyzed_at) "
            "VALUES (:pid, :score, :has_pool, NOW())"
        ), {"pid": property_id, "score": score, "has_pool": has_pool})
        session.execute(text(
            "UPDATE properties SET pool_detected = :detected WHERE id = :id"
        ), {"detected": has_pool, "id": property_id})
        session.commit()

    return {"property_id": property_id, "has_pool": has_pool, "score": round(score, 4)}


def _run_inference(img_bytes: bytes) -> tuple[float, bool]:
    """Run U-Net ONNX inference on aerial image bytes."""
    session = _get_session()
    if session is None:
        return 0.0, False

    img = Image.open(io.BytesIO(img_bytes)).convert("RGB").resize((256, 256))
    arr = np.array(img, dtype=np.float32) / 255.0
    arr = np.transpose(arr, (2, 0, 1))
    arr = np.expand_dims(arr, 0)

    outputs = session.run(None, {session.get_inputs()[0].name: arr})
    score = float(outputs[0].max())
    return score, score > DETECTION_THRESHOLD
