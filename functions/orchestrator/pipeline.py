"""Durable Functions orchestrators — pipeline coordination.

Uses fan-out/fan-in pattern:
  1. Ingest properties for a county (activity)
  2. Fan-out: detect pools for each property (parallel activities)
  3. Fan-out: generate designs for no-pool properties (parallel)
  4. Fan-out: enrich contacts (parallel)
"""

import azure.functions as func
import azure.durable_functions as df

bp = df.Blueprint()


# ---------------------------------------------------------------------------
# Orchestrator: Full Pipeline
# ---------------------------------------------------------------------------
@bp.orchestration_trigger(context_name="context")
def pipeline_orchestrator(context: df.DurableOrchestrationContext):
    """Run the full prospect pipeline for a county."""
    input_data = context.get_input()
    fips_code = input_data.get("fips_code", "12086")
    min_value = input_data.get("min_value", 1_000_000)

    # Step 1: Ingest properties
    property_ids = yield context.call_activity(
        "ingest_county_activity",
        {"fips_code": fips_code, "min_value": min_value},
    )

    if not property_ids:
        return {"status": "no_properties", "fips": fips_code}

    # Step 2: Fan-out pool detection
    detection_tasks = [
        context.call_activity("detect_pool_activity", {"property_id": pid})
        for pid in property_ids
    ]
    detection_results = yield context.task_all(detection_tasks)

    # Filter to properties without pools
    no_pool_ids = [
        r["property_id"] for r in detection_results
        if r.get("has_pool") is False
    ]

    if not no_pool_ids:
        return {"status": "all_have_pools", "fips": fips_code, "checked": len(property_ids)}

    # Step 3: Fan-out pool design generation
    design_tasks = [
        context.call_activity("generate_design_activity", {"property_id": pid})
        for pid in no_pool_ids
    ]
    yield context.task_all(design_tasks)

    # Step 4: Fan-out contact enrichment
    enrichment_tasks = [
        context.call_activity("enrich_contact_activity", {"property_id": pid})
        for pid in no_pool_ids
    ]
    yield context.task_all(enrichment_tasks)

    return {
        "status": "complete",
        "fips": fips_code,
        "total_ingested": len(property_ids),
        "no_pool_candidates": len(no_pool_ids),
        "designs_generated": len(no_pool_ids),
        "contacts_enriched": len(no_pool_ids),
    }


# ---------------------------------------------------------------------------
# HTTP Starter: Kick off the pipeline
# ---------------------------------------------------------------------------
@bp.route(route="start-pipeline", methods=["POST"])
@bp.durable_client_input(client_name="client")
async def start_pipeline(req: func.HttpRequest, client: df.DurableOrchestrationClient):
    """HTTP trigger to start the pipeline orchestration."""
    body = req.get_json()
    fips_code = body.get("fips_code", "12086")
    min_value = body.get("min_value", 1_000_000)

    instance_id = await client.start_new(
        "pipeline_orchestrator",
        client_input={"fips_code": fips_code, "min_value": min_value},
    )

    return client.create_check_status_response(req, instance_id)


# ---------------------------------------------------------------------------
# HTTP Starter: Run all Florida counties
# ---------------------------------------------------------------------------
@bp.route(route="start-all-counties", methods=["POST"])
@bp.durable_client_input(client_name="client")
async def start_all_counties(req: func.HttpRequest, client: df.DurableOrchestrationClient):
    """Start the pipeline for all configured Florida counties."""
    counties = ["12086", "12011", "12099", "12057", "12095", "12031", "12021", "12071", "12115"]
    instance_ids = []
    for fips in counties:
        iid = await client.start_new(
            "pipeline_orchestrator",
            client_input={"fips_code": fips, "min_value": 1_000_000},
        )
        instance_ids.append({"fips": fips, "instance_id": iid})

    return func.HttpResponse(
        body=str(instance_ids),
        status_code=202,
        mimetype="application/json",
    )


# ---------------------------------------------------------------------------
# Timer: Nightly pipeline trigger
# ---------------------------------------------------------------------------
@bp.timer_trigger(schedule="0 0 2 * * *", arg_name="timer", run_on_startup=False)
@bp.durable_client_input(client_name="client")
async def nightly_pipeline(timer: func.TimerRequest, client: df.DurableOrchestrationClient):
    """Run the full pipeline nightly at 2 AM UTC."""
    counties = ["12086", "12011", "12099", "12057", "12095", "12031"]
    for fips in counties:
        await client.start_new(
            "pipeline_orchestrator",
            client_input={"fips_code": fips, "min_value": 1_000_000},
        )
