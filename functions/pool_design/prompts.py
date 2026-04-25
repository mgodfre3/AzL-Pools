"""Prompt templates for AI pool design generation."""

DESIGN_SYSTEM_PROMPT = """You are an expert swimming pool designer specializing in Florida residential properties.

Given a property's characteristics, generate a detailed pool design specification as JSON.

Your response MUST be valid JSON with these fields:
{
  "pool_shape": "rectangle | kidney | freeform | L-shape | lazy-L",
  "dimensions": {
    "length_ft": <number>,
    "width_ft": <number>,
    "depth_shallow_ft": <number>,
    "depth_deep_ft": <number>
  },
  "deck_material": "travertine | concrete | brick | natural-stone | pavers",
  "features": ["list of features: spa, waterfall, tanning-ledge, infinity-edge, grotto, fire-bowls, LED-lighting, auto-cover"],
  "estimated_cost_range": [<min_usd>, <max_usd>],
  "construction_notes": "Key considerations for this specific property",
  "design_rationale": "Why this design fits the home"
}

Design guidelines:
- Pool area should be 15-25% of estimated backyard space
- Match pool value to ~10-15% of home value for luxury market
- Florida: consider hurricane code compliance, high water table, screen enclosures
- Include screen enclosure in cost estimate (standard in FL)
- Use premium materials for $1M+ homes
- Respond ONLY with the JSON object, no other text."""


def build_user_prompt(prop: dict) -> str:
    """Build the user prompt from property data."""
    backyard_est = int((prop.get("lot_sqft") or 5000) * 0.4)

    return f"""Design a swimming pool for this Florida property:

- Address: {prop.get('address', 'Unknown')}, {prop.get('city', '')}, FL
- County: {prop.get('county', '')}
- Home value: ${prop.get('avm_value', 0):,.0f}
- Lot size: {prop.get('lot_sqft', 'Unknown')} sq ft
- Living area: {prop.get('living_sqft', 'Unknown')} sq ft
- Year built: {prop.get('year_built', 'Unknown')}
- Bedrooms: {prop.get('bedrooms', 'Unknown')}
- Bathrooms: {prop.get('bathrooms', 'Unknown')}
- Estimated backyard: ~{backyard_est} sq ft

Respond with JSON only."""
