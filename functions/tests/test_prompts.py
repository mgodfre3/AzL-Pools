"""Tests for pool design prompts."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pool_design.prompts import build_user_prompt, DESIGN_SYSTEM_PROMPT


def test_build_user_prompt():
    prop = {
        "address": "123 Ocean Dr",
        "city": "Miami Beach",
        "county": "Miami-Dade",
        "avm_value": 2500000,
        "lot_sqft": 8000,
        "living_sqft": 4000,
        "year_built": 2015,
        "bedrooms": 5,
        "bathrooms": 4,
    }
    prompt = build_user_prompt(prop)
    assert "123 Ocean Dr" in prompt
    assert "$2,500,000" in prompt
    assert "8000" in prompt


def test_system_prompt_has_json_schema():
    assert "pool_shape" in DESIGN_SYSTEM_PROMPT
    assert "estimated_cost_range" in DESIGN_SYSTEM_PROMPT


def test_system_prompt_mentions_florida():
    assert "Florida" in DESIGN_SYSTEM_PROMPT or "FL" in DESIGN_SYSTEM_PROMPT
