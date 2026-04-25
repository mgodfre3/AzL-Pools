"""Pool design service tests."""

from prompts import build_user_prompt, DESIGN_SYSTEM_PROMPT


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
