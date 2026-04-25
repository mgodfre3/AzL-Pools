"""ATTOM Data Solutions API client."""

import httpx


class ATTOMClient:
    BASE_URL = "https://api.gateway.attomdata.com/propertyapi/v1.0.0"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {"apikey": api_key, "Accept": "application/json"}

    async def get_properties(
        self, fips: str, min_value: int = 1_000_000, page: int = 1, page_size: int = 100
    ) -> list[dict]:
        """Fetch properties from ATTOM assessment endpoint filtered by FIPS and min AVM value."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{self.BASE_URL}/assessment/detail",
                headers=self.headers,
                params={
                    "fips": fips,
                    "minavmvalue": min_value,
                    "pagesize": page_size,
                    "page": page,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("property", [])

    async def get_property_detail(self, attom_id: str) -> dict:
        """Fetch detailed property info by ATTOM ID."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{self.BASE_URL}/property/detail",
                headers=self.headers,
                params={"attomid": attom_id},
            )
            resp.raise_for_status()
            data = resp.json()
            properties = data.get("property", [])
            return properties[0] if properties else {}
