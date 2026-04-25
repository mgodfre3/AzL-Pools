"""AzL Pools — Contact Enrichment Service.

Enriches property owner contacts with phone/email from Melissa Data API
and stores results. Primary data source is Florida public records (mailing addresses).
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from melissa_client import MelissaClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://poolprospect:localdev@localhost:5432/poolprospect")
MELISSA_API_KEY = os.getenv("MELISSA_API_KEY", "")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
melissa = MelissaClient(api_key=MELISSA_API_KEY)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Contact enrichment service starting")
    yield


app = FastAPI(title="AzL Pools — Contact Enrichment", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/enrich/{property_id}")
async def enrich_contact(property_id: int):
    """Enrich owner contact info for a property."""
    with SessionLocal() as session:
        row = session.execute(
            text("SELECT id, owner_name, mailing_address FROM properties WHERE id = :id"),
            {"id": property_id},
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Property not found")

    owner_name = row[1] or ""
    mailing_address = row[2] or ""

    if not owner_name:
        return {"property_id": property_id, "status": "skipped", "reason": "no owner name"}

    # Enrich via Melissa Data
    enriched = {}
    if MELISSA_API_KEY:
        try:
            enriched = await melissa.lookup(owner_name, mailing_address)
        except Exception as e:
            logger.warning(f"Melissa enrichment failed for property {property_id}: {e}")

    # Store contact
    with SessionLocal() as session:
        session.execute(
            text(
                "INSERT INTO contacts (property_id, owner_name, mailing_address, phone, email, enrichment_src, enriched_at) "
                "VALUES (:pid, :name, :addr, :phone, :email, :src, NOW()) "
                "ON CONFLICT (property_id) DO UPDATE SET "
                "phone = COALESCE(EXCLUDED.phone, contacts.phone), "
                "email = COALESCE(EXCLUDED.email, contacts.email), "
                "enriched_at = NOW()"
            ),
            {
                "pid": property_id,
                "name": owner_name,
                "addr": mailing_address,
                "phone": enriched.get("phone"),
                "email": enriched.get("email"),
                "src": "melissa" if enriched else "public_records",
            },
        )
        session.commit()

    return {
        "property_id": property_id,
        "owner_name": owner_name,
        "mailing_address": mailing_address,
        "phone": enriched.get("phone"),
        "email": enriched.get("email"),
        "source": "melissa" if enriched else "public_records",
    }


@app.post("/batch-enrich")
async def batch_enrich(property_ids: list[int]):
    results = []
    for pid in property_ids:
        try:
            result = await enrich_contact(pid)
            results.append(result)
        except HTTPException as e:
            results.append({"property_id": pid, "error": e.detail})
    return {"results": results}


@app.get("/export/mailing-labels")
async def export_mailing_labels(limit: int = 100):
    """Export mailing labels for outreach as JSON (for PDF/CSV generation)."""
    with SessionLocal() as session:
        rows = session.execute(
            text(
                "SELECT c.owner_name, c.mailing_address, p.address, p.city, p.avm_value "
                "FROM contacts c JOIN properties p ON c.property_id = p.id "
                "WHERE p.pool_detected = false AND p.avm_value >= 1000000 "
                "ORDER BY p.avm_value DESC LIMIT :limit"
            ),
            {"limit": limit},
        ).fetchall()

    labels = [
        {
            "owner_name": r[0],
            "mailing_address": r[1],
            "property_address": r[2],
            "city": r[3],
            "home_value": float(r[4]) if r[4] else 0,
        }
        for r in rows
    ]
    return {"labels": labels, "count": len(labels)}
