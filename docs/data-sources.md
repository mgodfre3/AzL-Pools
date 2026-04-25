# Data Sources Guide

## ATTOM Data Solutions (Primary)

- **Website:** https://developer.attomdata.com/
- **Coverage:** Nationwide property data, FL-specific
- **Endpoints used:**
  - `/assessment/detail` — property valuations (AVM), filter by FIPS + min value
  - `/property/detail` — property characteristics including pool presence
  - `/sale/detail` — sale history
- **Pricing:** Custom/enterprise. Developer sandbox available.

## Florida County Property Appraisers (Supplemental, Free)

| County | Access Method | URL |
|--------|-------------|-----|
| Miami-Dade | REST API | `miamidade.gov/Apps/PA/PAWebApi/` |
| Broward | Web search | `web.bcpa.net` |
| Palm Beach | GIS/FTP | `pbcgov.org/papa/` |
| Hillsborough | CSV download | `hcpafl.org/Search/Data-Sets` |
| Orange | Web portal | `ocpafl.org` |
| Collier | Web portal | `collierappraiser.com` |

## Aerial Imagery

| Provider | API | Notes |
|----------|-----|-------|
| Bing Maps | REST Imagery API | Good free tier, check ToS for bulk |
| Google Maps | Static Maps API | $200/mo free credit |
| Nearmap | Licensed | Best for production, CV-friendly license |
| Maxar (DigitalGlobe) | Licensed | Highest resolution |

## Contact Enrichment

| Provider | Data | API |
|----------|------|-----|
| Melissa Data | Phone, email append | REST API, batch |
| TLOxp (TransUnion) | Skip-trace | Batch processing |
| CoreLogic | Full property + owner | Enterprise |
