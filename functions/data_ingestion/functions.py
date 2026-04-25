"""Data ingestion activity functions — ATTOM API property fetching."""

import logging
import azure.functions as func
import azure.durable_functions as df

from shared.config import ATTOM_API_KEY
from shared.db import SessionLocal
from data_ingestion.attom_client import ATTOMClient

logger = logging.getLogger(__name__)
bp = df.Blueprint()

FLORIDA_COUNTIES = {
    "12086": "Miami-Dade", "12011": "Broward", "12099": "Palm Beach",
    "12057": "Hillsborough", "12095": "Orange", "12031": "Duval",
    "12021": "Collier", "12071": "Lee", "12115": "Sarasota",
}

attom = ATTOMClient(api_key=ATTOM_API_KEY)


@bp.activity_trigger(input_name="input")
async def ingest_county_activity(input: dict) -> list[int]:
    """Fetch all $1M+ properties for a county from ATTOM and store in DB.

    Returns list of property IDs that need pool detection.
    """
    fips_code = input["fips_code"]
    min_value = input.get("min_value", 1_000_000)
    county_name = FLORIDA_COUNTIES.get(fips_code, fips_code)
    logger.info(f"Ingesting {county_name} (FIPS: {fips_code}), min value: ${min_value:,}")

    all_ids = []
    page = 1

    while True:
        try:
            properties = await attom.get_properties(fips_code, min_value=min_value, page=page)
        except Exception as e:
            logger.error(f"ATTOM error for {county_name} page {page}: {e}")
            break

        if not properties:
            break

        ids = _store_properties(properties, county_name)
        all_ids.extend(ids)
        logger.info(f"{county_name}: page {page}, stored {len(ids)} (total: {len(all_ids)})")
        page += 1

    # Return IDs of properties without confirmed pool status
    with SessionLocal() as session:
        from sqlalchemy import text
        rows = session.execute(text(
            "SELECT id FROM properties "
            "WHERE county = :county AND avm_value >= :min_val "
            "AND (has_pool = false OR has_pool IS NULL) "
            "AND pool_detected IS NULL"
        ), {"county": county_name, "min_val": min_value}).fetchall()
        return [r[0] for r in rows]


def _store_properties(raw_properties: list[dict], county: str) -> list[int]:
    """Upsert properties, return new IDs."""
    from sqlalchemy import text
    stored_ids = []

    with SessionLocal() as session:
        for prop in raw_properties:
            parcel_id = prop.get("identifier", {}).get("apn", "")
            if not parcel_id:
                continue

            addr = prop.get("address", {})
            assessment = prop.get("assessment", {})
            building = prop.get("building", {})
            loc = prop.get("location", {})
            summary = prop.get("summary", {})

            result = session.execute(text("""
                INSERT INTO properties (parcel_id, address, city, county, state, zip,
                    owner_name, mailing_address, avm_value, lot_sqft, living_sqft,
                    year_built, bedrooms, bathrooms, has_pool, latitude, longitude)
                VALUES (:parcel_id, :address, :city, :county, 'FL', :zip,
                    :owner_name, :mailing_address, :avm_value, :lot_sqft, :living_sqft,
                    :year_built, :bedrooms, :bathrooms, :has_pool, :lat, :lon)
                ON CONFLICT (parcel_id) DO UPDATE SET
                    avm_value = EXCLUDED.avm_value, updated_at = NOW()
                RETURNING id
            """), {
                "parcel_id": parcel_id,
                "address": addr.get("oneLine", ""),
                "city": addr.get("locality", ""),
                "county": county,
                "zip": addr.get("postal1", ""),
                "owner_name": assessment.get("owner", {}).get("owner1", {}).get("fullName", ""),
                "mailing_address": assessment.get("owner", {}).get("mailingAddressOneLine", ""),
                "avm_value": assessment.get("market", {}).get("mktTtlValue"),
                "lot_sqft": prop.get("lot", {}).get("lotSize1"),
                "living_sqft": building.get("size", {}).get("livingSize"),
                "year_built": summary.get("yearBuilt"),
                "bedrooms": building.get("rooms", {}).get("beds"),
                "bathrooms": building.get("rooms", {}).get("bathsFull"),
                "has_pool": summary.get("pool", False),
                "lat": loc.get("latitude"),
                "lon": loc.get("longitude"),
            })
            row = result.fetchone()
            if row:
                stored_ids.append(row[0])

        session.commit()
    return stored_ids


# ---------------------------------------------------------------------------
# Timer trigger: standalone nightly sync (non-orchestrated fallback)
# ---------------------------------------------------------------------------
@bp.timer_trigger(schedule="0 0 3 * * *", arg_name="timer", run_on_startup=False)
async def nightly_ingest(timer: func.TimerRequest):
    """Standalone nightly ingestion for all counties."""
    for fips in FLORIDA_COUNTIES:
        try:
            await ingest_county_activity({"fips_code": fips, "min_value": 1_000_000})
        except Exception as e:
            logger.error(f"Nightly ingest failed for {fips}: {e}")
