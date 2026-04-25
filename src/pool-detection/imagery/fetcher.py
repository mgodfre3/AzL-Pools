"""Aerial imagery fetcher — supports Bing Maps and Google Maps Static API."""

import os
import httpx

BING_MAPS_KEY = os.getenv("BING_MAPS_KEY", "")
GOOGLE_MAPS_KEY = os.getenv("GOOGLE_MAPS_KEY", "")
PROVIDER = os.getenv("IMAGERY_PROVIDER", "bing")


async def fetch_aerial_image(lat: float, lon: float, size: int = 500, zoom: int = 20) -> bytes:
    """Fetch a satellite/aerial image centered on the given coordinates."""
    if PROVIDER == "google" and GOOGLE_MAPS_KEY:
        return await _fetch_google(lat, lon, size, zoom)
    return await _fetch_bing(lat, lon, size, zoom)


async def _fetch_bing(lat: float, lon: float, size: int, zoom: int) -> bytes:
    url = (
        f"https://dev.virtualearth.net/REST/v1/Imagery/Map/Aerial/"
        f"{lat},{lon}/{zoom}?mapSize={size},{size}&key={BING_MAPS_KEY}"
    )
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content


async def _fetch_google(lat: float, lon: float, size: int, zoom: int) -> bytes:
    url = (
        f"https://maps.googleapis.com/maps/api/staticmap?"
        f"center={lat},{lon}&zoom={zoom}&size={size}x{size}"
        f"&maptype=satellite&key={GOOGLE_MAPS_KEY}"
    )
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content
