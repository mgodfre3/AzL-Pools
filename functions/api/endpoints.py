"""HTTP API endpoints for the dashboard backend."""

import json
import azure.functions as func
import azure.durable_functions as df
from sqlalchemy import text

from shared.db import SessionLocal

bp = df.Blueprint()


@bp.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
async def api_health(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(json.dumps({"status": "ok"}), mimetype="application/json")


@bp.route(route="stats", methods=["GET"])
async def api_stats(req: func.HttpRequest) -> func.HttpResponse:
    """Pipeline statistics."""
    with SessionLocal() as session:
        total = session.execute(text("SELECT COUNT(*) FROM properties")).scalar() or 0
        million = session.execute(text("SELECT COUNT(*) FROM properties WHERE avm_value >= 1000000")).scalar() or 0
        no_pool = session.execute(text(
            "SELECT COUNT(*) FROM properties WHERE pool_detected = false AND avm_value >= 1000000"
        )).scalar() or 0
        designs = session.execute(text("SELECT COUNT(*) FROM pool_designs")).scalar() or 0
        contacts = session.execute(text("SELECT COUNT(*) FROM contacts")).scalar() or 0
        sent = session.execute(text("SELECT COUNT(*) FROM outreach WHERE status = 'sent'")).scalar() or 0

    return func.HttpResponse(json.dumps({
        "total_properties": total, "million_plus": million,
        "no_pool_candidates": no_pool, "designs_generated": designs,
        "contacts_enriched": contacts, "outreach_sent": sent,
    }), mimetype="application/json")


@bp.route(route="properties", methods=["GET"])
async def api_properties(req: func.HttpRequest) -> func.HttpResponse:
    """List properties with filtering."""
    page = int(req.params.get("page", "1"))
    per_page = min(int(req.params.get("per_page", "50")), 200)
    county = req.params.get("county")
    offset = (page - 1) * per_page

    conditions = ["1=1"]
    params = {"limit": per_page, "offset": offset}
    if county:
        conditions.append("county = :county")
        params["county"] = county

    where = " AND ".join(conditions)

    with SessionLocal() as session:
        rows = session.execute(text(
            f"SELECT id, parcel_id, address, city, county, avm_value, lot_sqft, "
            f"has_pool, pool_detected, owner_name "
            f"FROM properties WHERE {where} ORDER BY avm_value DESC LIMIT :limit OFFSET :offset"
        ), params).fetchall()
        total = session.execute(text(f"SELECT COUNT(*) FROM properties WHERE {where}"), params).scalar()

    data = [
        {"id": r[0], "parcel_id": r[1], "address": r[2], "city": r[3], "county": r[4],
         "avm_value": float(r[5]) if r[5] else None, "lot_sqft": r[6],
         "has_pool": r[7], "pool_detected": r[8], "owner_name": r[9]}
        for r in rows
    ]
    return func.HttpResponse(
        json.dumps({"properties": data, "total": total, "page": page}),
        mimetype="application/json",
    )


@bp.route(route="leads", methods=["GET"])
async def api_leads(req: func.HttpRequest) -> func.HttpResponse:
    """Top leads: $1M+ homes without pools that have designs + contacts."""
    limit = min(int(req.params.get("limit", "100")), 1000)

    with SessionLocal() as session:
        rows = session.execute(text(
            "SELECT p.id, p.address, p.city, p.county, p.avm_value, "
            "c.owner_name, c.mailing_address, c.phone, c.email, pd.design_output "
            "FROM properties p "
            "JOIN contacts c ON c.property_id = p.id "
            "JOIN pool_designs pd ON pd.property_id = p.id "
            "WHERE p.pool_detected = false AND p.avm_value >= 1000000 "
            "ORDER BY p.avm_value DESC LIMIT :limit"
        ), {"limit": limit}).fetchall()

    leads = [
        {"property_id": r[0], "address": r[1], "city": r[2], "county": r[3],
         "home_value": float(r[4]) if r[4] else 0,
         "owner_name": r[5], "mailing_address": r[6], "phone": r[7], "email": r[8],
         "pool_design": r[9]}
        for r in rows
    ]
    return func.HttpResponse(
        json.dumps({"leads": leads, "count": len(leads)}),
        mimetype="application/json",
    )


@bp.route(route="export/mailing-labels", methods=["GET"])
async def api_mailing_labels(req: func.HttpRequest) -> func.HttpResponse:
    """Export mailing labels for direct mail outreach."""
    limit = min(int(req.params.get("limit", "100")), 5000)

    with SessionLocal() as session:
        rows = session.execute(text(
            "SELECT c.owner_name, c.mailing_address, p.address, p.city, p.avm_value "
            "FROM contacts c JOIN properties p ON c.property_id = p.id "
            "WHERE p.pool_detected = false AND p.avm_value >= 1000000 "
            "ORDER BY p.avm_value DESC LIMIT :limit"
        ), {"limit": limit}).fetchall()

    labels = [
        {"owner_name": r[0], "mailing_address": r[1], "property_address": r[2],
         "city": r[3], "home_value": float(r[4]) if r[4] else 0}
        for r in rows
    ]
    return func.HttpResponse(
        json.dumps({"labels": labels, "count": len(labels)}),
        mimetype="application/json",
    )
