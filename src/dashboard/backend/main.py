"""AzL Pools — Dashboard Backend.

FastAPI backend serving the React frontend and providing API endpoints
for lead management, property browsing, design previews, and export.
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://poolprospect:localdev@localhost:5432/poolprospect")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Dashboard backend starting")
    yield


app = FastAPI(title="AzL Pools — Dashboard", lifespan=lifespan)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/stats")
async def dashboard_stats():
    """Get high-level pipeline statistics."""
    with SessionLocal() as session:
        total = session.execute(text("SELECT COUNT(*) FROM properties")).scalar() or 0
        million_plus = session.execute(
            text("SELECT COUNT(*) FROM properties WHERE avm_value >= 1000000")
        ).scalar() or 0
        no_pool = session.execute(
            text("SELECT COUNT(*) FROM properties WHERE pool_detected = false AND avm_value >= 1000000")
        ).scalar() or 0
        designs = session.execute(text("SELECT COUNT(*) FROM pool_designs")).scalar() or 0
        contacts = session.execute(text("SELECT COUNT(*) FROM contacts")).scalar() or 0
        sent = session.execute(
            text("SELECT COUNT(*) FROM outreach WHERE status = 'sent'")
        ).scalar() or 0

    return {
        "total_properties": total,
        "million_plus": million_plus,
        "no_pool_candidates": no_pool,
        "designs_generated": designs,
        "contacts_enriched": contacts,
        "outreach_sent": sent,
    }


@app.get("/api/properties")
async def list_properties(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    county: str | None = None,
    min_value: float | None = None,
    has_pool: bool | None = None,
    pool_detected: bool | None = None,
):
    """List properties with filtering and pagination."""
    offset = (page - 1) * per_page
    conditions = ["1=1"]
    params: dict = {"limit": per_page, "offset": offset}

    if county:
        conditions.append("county = :county")
        params["county"] = county
    if min_value:
        conditions.append("avm_value >= :min_value")
        params["min_value"] = min_value
    if has_pool is not None:
        conditions.append("has_pool = :has_pool")
        params["has_pool"] = has_pool
    if pool_detected is not None:
        conditions.append("pool_detected = :pool_detected")
        params["pool_detected"] = pool_detected

    where_clause = " AND ".join(conditions)

    with SessionLocal() as session:
        rows = session.execute(
            text(
                f"SELECT id, parcel_id, address, city, county, avm_value, lot_sqft, "
                f"has_pool, pool_detected, owner_name "
                f"FROM properties WHERE {where_clause} "
                f"ORDER BY avm_value DESC LIMIT :limit OFFSET :offset"
            ),
            params,
        ).fetchall()

        total = session.execute(
            text(f"SELECT COUNT(*) FROM properties WHERE {where_clause}"),
            params,
        ).scalar()

    properties = [
        {
            "id": r[0], "parcel_id": r[1], "address": r[2], "city": r[3],
            "county": r[4], "avm_value": float(r[5]) if r[5] else None,
            "lot_sqft": r[6], "has_pool": r[7], "pool_detected": r[8],
            "owner_name": r[9],
        }
        for r in rows
    ]

    return {"properties": properties, "total": total, "page": page, "per_page": per_page}


@app.get("/api/properties/{property_id}")
async def get_property(property_id: int):
    """Get full property detail with design and contact info."""
    with SessionLocal() as session:
        prop = session.execute(
            text("SELECT * FROM properties WHERE id = :id"), {"id": property_id}
        ).fetchone()

        if not prop:
            return {"error": "not found"}, 404

        design = session.execute(
            text("SELECT design_output FROM pool_designs WHERE property_id = :id ORDER BY created_at DESC LIMIT 1"),
            {"id": property_id},
        ).fetchone()

        contact = session.execute(
            text("SELECT owner_name, mailing_address, phone, email FROM contacts WHERE property_id = :id"),
            {"id": property_id},
        ).fetchone()

    return {
        "property": dict(prop._mapping),
        "design": dict(design._mapping) if design else None,
        "contact": dict(contact._mapping) if contact else None,
    }


@app.get("/api/leads")
async def get_leads(limit: int = Query(100, ge=1, le=1000)):
    """Get top leads: $1M+ homes without pools that have designs and contacts."""
    with SessionLocal() as session:
        rows = session.execute(
            text(
                "SELECT p.id, p.address, p.city, p.county, p.avm_value, "
                "c.owner_name, c.mailing_address, c.phone, c.email, "
                "pd.design_output "
                "FROM properties p "
                "JOIN contacts c ON c.property_id = p.id "
                "JOIN pool_designs pd ON pd.property_id = p.id "
                "WHERE p.pool_detected = false AND p.avm_value >= 1000000 "
                "ORDER BY p.avm_value DESC LIMIT :limit"
            ),
            {"limit": limit},
        ).fetchall()

    leads = [
        {
            "property_id": r[0], "address": r[1], "city": r[2], "county": r[3],
            "home_value": float(r[4]) if r[4] else 0,
            "owner_name": r[5], "mailing_address": r[6],
            "phone": r[7], "email": r[8],
            "pool_design": r[9],
        }
        for r in rows
    ]
    return {"leads": leads, "count": len(leads)}
