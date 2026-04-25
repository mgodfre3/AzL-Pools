"""Pool design activity — calls Azure OpenAI to generate pool designs."""

import json
import logging

import azure.durable_functions as df
from openai import AzureOpenAI
from sqlalchemy import text

from shared.config import AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY, AZURE_OPENAI_DEPLOYMENT
from shared.db import SessionLocal
from pool_design.prompts import DESIGN_SYSTEM_PROMPT, build_user_prompt

logger = logging.getLogger(__name__)
bp = df.Blueprint()

_client = None


def _get_client():
    global _client
    if _client is None and AZURE_OPENAI_ENDPOINT:
        _client = AzureOpenAI(
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_key=AZURE_OPENAI_KEY,
            api_version="2024-10-21",
        )
    return _client


@bp.activity_trigger(input_name="input")
async def generate_design_activity(input: dict) -> dict:
    """Generate an AI pool design for a property."""
    property_id = input["property_id"]

    with SessionLocal() as session:
        row = session.execute(text(
            "SELECT id, address, city, county, avm_value, lot_sqft, living_sqft, "
            "year_built, bedrooms, bathrooms FROM properties WHERE id = :id"
        ), {"id": property_id}).fetchone()

    if not row:
        return {"property_id": property_id, "error": "not found"}

    prop = dict(row._mapping)
    user_prompt = build_user_prompt(prop)

    client = _get_client()
    if not client:
        return {"property_id": property_id, "error": "no AI endpoint configured"}

    try:
        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": DESIGN_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=1200,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        design = json.loads(raw)
    except json.JSONDecodeError:
        design = {"raw_response": raw}
    except Exception as e:
        logger.error(f"AI design error for property {property_id}: {e}")
        return {"property_id": property_id, "error": str(e)}

    with SessionLocal() as session:
        session.execute(text(
            "INSERT INTO pool_designs (property_id, design_params, design_output, created_at) "
            "VALUES (:pid, :params, :output, NOW())"
        ), {
            "pid": property_id,
            "params": json.dumps({"lot_sqft": prop.get("lot_sqft"), "living_sqft": prop.get("living_sqft")}),
            "output": json.dumps(design),
        })
        session.commit()

    return {"property_id": property_id, "design": design}
