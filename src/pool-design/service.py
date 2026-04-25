"""AzL Pools — Pool Design Generator Service.

Calls Foundry Local (Phi-4-mini, CPU) to generate parametric pool designs
based on property characteristics.
"""

import os
import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from openai import OpenAI
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from prompts import DESIGN_SYSTEM_PROMPT, build_user_prompt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://poolprospect:localdev@localhost:5432/poolprospect")
FOUNDRY_LOCAL_URL = os.getenv("FOUNDRY_LOCAL_URL", "http://localhost:5273/v1")
FOUNDRY_MODEL = os.getenv("FOUNDRY_MODEL", "phi-4-mini")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

client = OpenAI(base_url=FOUNDRY_LOCAL_URL, api_key="not-needed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Pool design service starting — model: {FOUNDRY_MODEL} at {FOUNDRY_LOCAL_URL}")
    yield


app = FastAPI(title="AzL Pools — Pool Design Generator", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok", "model": FOUNDRY_MODEL}


@app.post("/design/{property_id}")
async def generate_design(property_id: int):
    """Generate an AI pool design for a property."""
    with SessionLocal() as session:
        row = session.execute(
            text(
                "SELECT id, address, city, county, avm_value, lot_sqft, living_sqft, "
                "year_built, bedrooms, bathrooms FROM properties WHERE id = :id"
            ),
            {"id": property_id},
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Property not found")

    prop = dict(row._mapping)
    user_prompt = build_user_prompt(prop)

    try:
        response = client.chat.completions.create(
            model=FOUNDRY_MODEL,
            messages=[
                {"role": "system", "content": DESIGN_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=1200,
        )
        raw_content = response.choices[0].message.content

        # Parse JSON from response (handle markdown code blocks)
        json_str = raw_content.strip()
        if json_str.startswith("```"):
            json_str = json_str.split("\n", 1)[1].rsplit("```", 1)[0]
        design = json.loads(json_str)

    except json.JSONDecodeError:
        logger.warning(f"Failed to parse JSON for property {property_id}, storing raw")
        design = {"raw_response": raw_content}
    except Exception as e:
        logger.error(f"Foundry Local error for property {property_id}: {e}")
        raise HTTPException(status_code=502, detail="AI design generation failed")

    # Store design
    with SessionLocal() as session:
        session.execute(
            text(
                "INSERT INTO pool_designs (property_id, design_params, design_output, created_at) "
                "VALUES (:pid, :params, :output, NOW())"
            ),
            {
                "pid": property_id,
                "params": json.dumps({"lot_sqft": prop["lot_sqft"], "living_sqft": prop["living_sqft"]}),
                "output": json.dumps(design),
            },
        )
        session.commit()

    logger.info(f"Generated pool design for property {property_id}")
    return {"property_id": property_id, "design": design}


@app.post("/batch-design")
async def batch_design(property_ids: list[int]):
    results = []
    for pid in property_ids:
        try:
            result = await generate_design(pid)
            results.append(result)
        except HTTPException as e:
            results.append({"property_id": pid, "error": e.detail})
    return {"results": results}
