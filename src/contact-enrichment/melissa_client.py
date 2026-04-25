"""Melissa Data API client for contact enrichment."""

import httpx


class MelissaClient:
    BASE_URL = "https://personator.melissadata.net/v3/WEB/ContactVerify/doContactVerify"

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def lookup(self, full_name: str, address: str) -> dict:
        """Look up phone and email for a person by name and address."""
        if not self.api_key:
            return {}

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                self.BASE_URL,
                params={
                    "id": self.api_key,
                    "full": full_name,
                    "a1": address,
                    "cols": "Phone,Email",
                    "format": "json",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        records = data.get("Records", [])
        if not records:
            return {}

        record = records[0]
        return {
            "phone": record.get("PhoneNumber") or None,
            "email": record.get("EmailAddress") or None,
        }
