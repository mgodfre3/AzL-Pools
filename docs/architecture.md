# AzL Pools — Architecture

## System Overview

**Azure Functions** (Python v2) with **Durable Functions** orchestration,
backed by Azure PostgreSQL, Azure Storage queues, and Azure OpenAI.

```
HTTP/Timer Trigger
        │
        ▼
┌─────────────────────────────────────────────┐
│  Durable Orchestrator (pipeline_orchestrator)│
│                                             │
│  1. ingest_county_activity   (ATTOM API)    │
│  2. detect_pool_activity     (U-Net ONNX)   │  ← fan-out/fan-in
│  3. generate_design_activity (Azure OpenAI)  │  ← fan-out/fan-in
│  4. enrich_contact_activity  (Melissa API)   │  ← fan-out/fan-in
└──────────────┬──────────────────────────────┘
               │
    ┌──────────┼──────────┐
    ▼          ▼          ▼
PostgreSQL   Storage   App Insights
```

## Service Map

| Function | Trigger | Purpose |
|----------|---------|---------|
| pipeline_orchestrator | Durable | Coordinates full pipeline |
| start_pipeline | HTTP POST | Starts orchestration for a county |
| nightly_pipeline | Timer (2 AM) | Nightly auto-run |
| ingest_county_activity | Activity | ATTOM API property fetch |
| detect_pool_activity | Activity | Aerial image + ONNX inference |
| generate_design_activity | Activity | Azure OpenAI pool design |
| enrich_contact_activity | Activity | Melissa skip-trace enrichment |
| api_stats | HTTP GET | Dashboard statistics |
| api_properties | HTTP GET | Property listing |
| api_leads | HTTP GET | Top lead listing |
| api_mailing_labels | HTTP GET | Export mailing labels |

## Marketplace Packaging

Packaged as an Azure Managed Application:
- `marketplace/arm/mainTemplate.json` — ARM template deploying all resources
- `marketplace/ui/createUiDefinition.json` — Portal wizard (4 steps)
- Published via Partner Center as an Azure Application offer
