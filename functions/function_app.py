"""AzL Pools — Azure Functions Application (Python v2 model).

Main entry point registering all function triggers:
- Timer: nightly data ingestion
- Queue: pool detection, pool design, contact enrichment
- HTTP: dashboard API endpoints
- Durable: pipeline orchestrator
"""

import azure.functions as func
import azure.durable_functions as df

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)
bp_orchestrator = df.Blueprint()

# ---------------------------------------------------------------------------
# Import and register blueprints
# ---------------------------------------------------------------------------
from orchestrator.pipeline import bp as orchestrator_bp
from data_ingestion.functions import bp as ingestion_bp
from pool_detection.functions import bp as detection_bp
from pool_design.functions import bp as design_bp
from contact_enrichment.functions import bp as enrichment_bp
from api.endpoints import bp as api_bp

app.register_functions(orchestrator_bp)
app.register_functions(ingestion_bp)
app.register_functions(detection_bp)
app.register_functions(design_bp)
app.register_functions(enrichment_bp)
app.register_functions(api_bp)
