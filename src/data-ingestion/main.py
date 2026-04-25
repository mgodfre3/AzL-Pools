"""AzL Pools — Data Ingestion Service.

Fetches property data from ATTOM API and Florida county appraiser records.
Filters for homes valued >= $1M and enqueues them for pool detection.
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, BackgroundTasks, HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from attom_client import ATTOMClient
from models import Property

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://poolprospect:localdev@localhost:5432/poolprospect")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
attom = ATTOMClient(api_key=os.getenv("ATTOM_API_KEY", ""))

FLORIDA_COUNTIES = {
    "12086": "Miami-Dade",
    "12011": "Broward",
    "12099": "Palm Beach",
    "12057": "Hillsborough",
    "12095": "Orange",
    "12031": "Duval",
    "12021": "Collier",
    "12071": "Lee",
    "12115": "Sarasota",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Data ingestion service starting")
    yield
    logger.info("Data ingestion service shutting down")


app = FastAPI(title="AzL Pools — Data Ingestion", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/stats")
async def stats():
    with SessionLocal() as session:
        total = session.execute(text("SELECT COUNT(*) FROM properties")).scalar()
        million_plus = session.execute(
            text("SELECT COUNT(*) FROM properties WHERE avm_value >= 1000000")
        ).scalar()
        no_pool = session.execute(
            text("SELECT COUNT(*) FROM properties WHERE avm_value >= 1000000 AND (has_pool = false OR has_pool IS NULL)")
        ).scalar()
    return {"total_properties": total, "million_plus": million_plus, "no_pool_candidates": no_pool}


@app.post("/ingest/county/{fips_code}")
async def ingest_county(fips_code: str, background_tasks: BackgroundTasks):
    if fips_code not in FLORIDA_COUNTIES:
        raise HTTPException(status_code=400, detail=f"Unknown FIPS code. Valid: {list(FLORIDA_COUNTIES.keys())}")
    background_tasks.add_task(fetch_and_store_county, fips_code)
    return {"status": "ingestion_started", "county": FLORIDA_COUNTIES[fips_code], "fips": fips_code}


@app.post("/ingest/all")
async def ingest_all(background_tasks: BackgroundTasks):
    for fips in FLORIDA_COUNTIES:
        background_tasks.add_task(fetch_and_store_county, fips)
    return {"status": "ingestion_started", "counties": len(FLORIDA_COUNTIES)}


async def fetch_and_store_county(fips_code: str):
    county_name = FLORIDA_COUNTIES.get(fips_code, fips_code)
    logger.info(f"Starting ingestion for {county_name} (FIPS: {fips_code})")
    page = 1
    total_stored = 0

    while True:
        try:
            properties = await attom.get_properties(fips_code, min_value=1_000_000, page=page, page_size=100)
        except Exception as e:
            logger.error(f"ATTOM API error for {county_name} page {page}: {e}")
            break

        if not properties:
            break

        stored = store_properties(properties, county_name)
        total_stored += stored
        logger.info(f"{county_name}: page {page}, stored {stored} properties (total: {total_stored})")
        page += 1

    logger.info(f"Completed ingestion for {county_name}: {total_stored} properties")


def store_properties(raw_properties: list[dict], county: str) -> int:
    """Upsert properties into the database."""
    stored = 0
    with SessionLocal() as session:
        for prop in raw_properties:
            parcel_id = prop.get("identifier", {}).get("apn", "")
            if not parcel_id:
                continue

            existing = session.query(Property).filter_by(parcel_id=parcel_id).first()
            address_info = prop.get("address", {})
            assessment = prop.get("assessment", {})
            building = prop.get("building", {})
            lot = prop.get("lot", {})
            location = prop.get("location", {})
            summary = prop.get("summary", {})

            values = {
                "address": address_info.get("oneLine", ""),
                "city": address_info.get("locality", ""),
                "county": county,
                "state": "FL",
                "zip": address_info.get("postal1", ""),
                "owner_name": prop.get("assessment", {}).get("owner", {}).get("owner1", {}).get("fullName", ""),
                "mailing_address": prop.get("assessment", {}).get("owner", {}).get("mailingAddressOneLine", ""),
                "avm_value": assessment.get("market", {}).get("mktTtlValue"),
                "lot_sqft": lot.get("lotSize1"),
                "living_sqft": building.get("size", {}).get("livingSize"),
                "year_built": summary.get("yearBuilt"),
                "bedrooms": building.get("rooms", {}).get("beds"),
                "bathrooms": building.get("rooms", {}).get("bathsFull"),
                "has_pool": summary.get("pool", False),
                "latitude": location.get("latitude"),
                "longitude": location.get("longitude"),
            }

            if existing:
                for key, val in values.items():
                    if val is not None:
                        setattr(existing, key, val)
            else:
                new_prop = Property(parcel_id=parcel_id, **values)
                session.add(new_prop)
                stored += 1

        session.commit()
    return stored
