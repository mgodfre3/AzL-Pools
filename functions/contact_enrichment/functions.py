"""Contact enrichment activity — Melissa Data API lookup."""

import logging

import azure.durable_functions as df
from sqlalchemy import text

from shared.config import MELISSA_API_KEY
from shared.db import SessionLocal

logger = logging.getLogger(__name__)
bp = df.Blueprint()


@bp.activity_trigger(input_name="input")
async def enrich_contact_activity(input: dict) -> dict:
    """Enrich a property owner's contact info via Melissa Data."""
    property_id = input["property_id"]

    with SessionLocal() as session:
        row = session.execute(
            text("SELECT owner_name, mailing_address FROM properties WHERE id = :id"),
            {"id": property_id},
        ).fetchone()

    if not row or not row[0]:
        return {"property_id": property_id, "status": "skipped", "reason": "no owner"}

    owner_name, mailing_address = row[0], row[1] or ""
    enriched = {}

    if MELISSA_API_KEY:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    "https://personator.melissadata.net/v3/WEB/ContactVerify/doContactVerify",
                    params={
                        "id": MELISSA_API_KEY,
                        "full": owner_name,
                        "a1": mailing_address,
                        "cols": "Phone,Email",
                        "format": "json",
                    },
                )
                resp.raise_for_status()
                records = resp.json().get("Records", [])
                if records:
                    enriched = {
                        "phone": records[0].get("PhoneNumber") or None,
                        "email": records[0].get("EmailAddress") or None,
                    }
        except Exception as e:
            logger.warning(f"Melissa enrichment failed for property {property_id}: {e}")

    with SessionLocal() as session:
        session.execute(text(
            "INSERT INTO contacts (property_id, owner_name, mailing_address, phone, email, enrichment_src, enriched_at) "
            "VALUES (:pid, :name, :addr, :phone, :email, :src, NOW()) "
            "ON CONFLICT DO NOTHING"
        ), {
            "pid": property_id,
            "name": owner_name,
            "addr": mailing_address,
            "phone": enriched.get("phone"),
            "email": enriched.get("email"),
            "src": "melissa" if enriched else "public_records",
        })
        session.commit()

    return {
        "property_id": property_id,
        "owner_name": owner_name,
        "phone": enriched.get("phone"),
        "email": enriched.get("email"),
    }
