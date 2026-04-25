-- AzL Pools: Initial Schema
-- PostGIS extension for spatial queries
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE properties (
    id              SERIAL PRIMARY KEY,
    parcel_id       VARCHAR(50) UNIQUE NOT NULL,
    address         TEXT NOT NULL,
    city            VARCHAR(100),
    county          VARCHAR(100),
    state           VARCHAR(2) DEFAULT 'FL',
    zip             VARCHAR(10),
    owner_name      TEXT,
    mailing_address TEXT,
    avm_value       NUMERIC(12, 2),
    lot_sqft        INTEGER,
    living_sqft     INTEGER,
    year_built      INTEGER,
    bedrooms        INTEGER,
    bathrooms       NUMERIC(3, 1),
    has_pool        BOOLEAN DEFAULT NULL,
    pool_detected   BOOLEAN DEFAULT NULL,
    latitude        NUMERIC(10, 7),
    longitude       NUMERIC(10, 7),
    geom            GEOMETRY(Point, 4326),
    ingested_at     TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_properties_county ON properties (county);
CREATE INDEX idx_properties_avm ON properties (avm_value);
CREATE INDEX idx_properties_pool ON properties (has_pool, pool_detected);
CREATE INDEX idx_properties_geom ON properties USING GIST (geom);

CREATE TABLE pool_analysis (
    id              SERIAL PRIMARY KEY,
    property_id     INTEGER REFERENCES properties(id) ON DELETE CASCADE,
    image_url       TEXT,
    detection_score NUMERIC(5, 4),
    has_pool        BOOLEAN,
    analyzed_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_pool_analysis_property ON pool_analysis (property_id);

CREATE TABLE pool_designs (
    id              SERIAL PRIMARY KEY,
    property_id     INTEGER REFERENCES properties(id) ON DELETE CASCADE,
    design_params   JSONB,
    design_output   JSONB,
    render_path     TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_pool_designs_property ON pool_designs (property_id);

CREATE TABLE contacts (
    id              SERIAL PRIMARY KEY,
    property_id     INTEGER REFERENCES properties(id) ON DELETE CASCADE,
    owner_name      TEXT,
    mailing_address TEXT,
    phone           TEXT,
    email           TEXT,
    enrichment_src  VARCHAR(50),
    enriched_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_contacts_property ON contacts (property_id);

CREATE TABLE outreach (
    id              SERIAL PRIMARY KEY,
    contact_id      INTEGER REFERENCES contacts(id) ON DELETE CASCADE,
    design_id       INTEGER REFERENCES pool_designs(id) ON DELETE SET NULL,
    channel         VARCHAR(20),
    status          VARCHAR(20) DEFAULT 'pending',
    sent_at         TIMESTAMPTZ,
    response        TEXT
);

CREATE INDEX idx_outreach_status ON outreach (status);
