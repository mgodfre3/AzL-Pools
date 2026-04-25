"""Shared configuration — reads from Azure Functions app settings."""

import os


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://poolprospect:localdev@localhost:5432/poolprospect")
ATTOM_API_KEY = os.getenv("ATTOM_API_KEY", "")
BING_MAPS_KEY = os.getenv("BING_MAPS_KEY", "")
MELISSA_API_KEY = os.getenv("MELISSA_API_KEY", "")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY", "")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "phi-4-mini")
DETECTION_THRESHOLD = float(os.getenv("DETECTION_THRESHOLD", "0.5"))
