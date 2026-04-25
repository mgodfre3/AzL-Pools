"""CLI entry point for background tasks (used by CronJob)."""

import asyncio
import sys
import os
import logging

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://poolprospect:localdev@localhost:5432/poolprospect")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


async def sync_all_counties():
    """Trigger ingestion for all configured Florida counties."""
    from main import fetch_and_store_county, FLORIDA_COUNTIES

    for fips in FLORIDA_COUNTIES:
        await fetch_and_store_county(fips)


async def enqueue_detection_for_candidates():
    """Find $1M+ homes without pool detection results and enqueue them."""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "shared", "queue"))
    from tasks import enqueue_detection

    with Session() as session:
        rows = session.execute(text(
            "SELECT id FROM properties "
            "WHERE avm_value >= 1000000 "
            "AND (has_pool = false OR has_pool IS NULL) "
            "AND pool_detected IS NULL "
            "LIMIT 1000"
        )).fetchall()

    logger.info(f"Enqueuing {len(rows)} properties for pool detection")
    for row in rows:
        await enqueue_detection(row[0])


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "sync-all-counties"

    if command == "sync-all-counties":
        asyncio.run(sync_all_counties())
    elif command == "enqueue-detection":
        asyncio.run(enqueue_detection_for_candidates())
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
