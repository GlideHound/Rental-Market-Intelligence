-- create_warehouse_rentals.sql
-- Purpose: create warehouse dimension and fact tables from staging data
DROP TABLE IF EXISTS warehouse.fact_rental_listing_snapshot;
DROP TABLE IF EXISTS warehouse.dim_listing;
DROP TABLE IF EXISTS warehouse.dim_location;
DROP TABLE IF EXISTS warehouse.dim_property;
DROP TABLE IF EXISTS warehouse.dim_date;

CREATE TABLE warehouse.dim_listing (
    listing_key SERIAL PRIMARY KEY,
    listing_name TEXT,
    listing_id TEXT NOT NULL UNIQUE,
    created_date TIMESTAMP,
    modified_date TIMESTAMP,
    verified BOOLEAN
);

CREATE TABLE warehouse.dim_location (
    location_key SERIAL PRIMARY KEY,
    street TEXT,
    postal_code TEXT,
    postal_fsa TEXT,
    longitude DOUBLE PRECISION,
    latitude DOUBLE PRECISION
);

CREATE TABLE warehouse.dim_property (
    property_key SERIAL PRIMARY KEY,
    property_type TEXT NOT NULL,
    property_group TEXT NOT NULL,
    is_auxiliary_listing BOOLEAN NOT NULL
);

CREATE TABLE warehouse.dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    day INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month_name TEXT NOT NULL,
    day_of_week TEXT NOT NULL
);

CREATE TABLE warehouse.fact_rental_listing_snapshot (
    snapshot_key SERIAL PRIMARY KEY,

    -- Foreign keys to dimension tables
    listing_key INTEGER NOT NULL,
    location_key INTEGER NOT NULL,
    property_key INTEGER NOT NULL,
    date_key INTEGER NOT NULL,

    -- Rent measures
    rent_min NUMERIC,
    rent_max NUMERIC,
    rent_representative NUMERIC,
    rent_bound_type TEXT,

    -- Unit attributes / measures
    beds_avg NUMERIC,
    bath_avg NUMERIC,
    size_avg NUMERIC,

    -- Derived measures
    rent_per_bed NUMERIC,
    rent_per_sqft NUMERIC,

    -- Other measurable listing attributes
    images_count INTEGER,

    -- Exact pipeline load timestamp
    loaded_at TIMESTAMP,

    -- Foreign key constraints
    CONSTRAINT fk_fact_listing
        FOREIGN KEY (listing_key)
        REFERENCES warehouse.dim_listing(listing_key),

    CONSTRAINT fk_fact_location
        FOREIGN KEY (location_key)
        REFERENCES warehouse.dim_location(location_key),

    CONSTRAINT fk_fact_property
        FOREIGN KEY (property_key)
        REFERENCES warehouse.dim_property(property_key),

    CONSTRAINT fk_fact_date
        FOREIGN KEY (date_key)
        REFERENCES warehouse.dim_date(date_key)
);

WITH latest_listing AS (
    SELECT
        listing_id,
        listing_name,
        street,
        created_date,
        modified_date,
        verified,
        loaded_at,
        ROW_NUMBER() OVER (
            PARTITION BY listing_id
            ORDER BY loaded_at DESC NULLS LAST
        ) AS rn
    FROM staging.stg_rental_listings
    WHERE listing_id IS NOT NULL
)

INSERT INTO warehouse.dim_listing (
    listing_id,
    listing_name,
    created_date,
    modified_date,
    verified
)
SELECT
    listing_id,
    listing_name,
    created_date,
    modified_date,
    verified
FROM latest_listing
WHERE rn = 1;

WITH location_source AS (
    SELECT DISTINCT
        street,
        postal_code,
        CASE
            WHEN postal_code IS NOT NULL AND LENGTH(postal_code) >= 3
                THEN LEFT(postal_code, 3)
            ELSE NULL
        END AS postal_fsa,
        longitude,
        latitude
    FROM staging.stg_rental_listings
    WHERE street IS NOT NULL
       OR postal_code IS NOT NULL
       OR longitude IS NOT NULL
       OR latitude IS NOT NULL
)

INSERT INTO warehouse.dim_location (
    street,
    postal_code,
    postal_fsa,
    longitude,
    latitude
)
SELECT
    street,
    postal_code,
    postal_fsa,
    longitude,
    latitude
FROM location_source;


-- NEED MORE WORK DETERMINE THE AUXILIARY, CHECK ALL UNIQUE TYPES
WITH property_source AS (
    SELECT DISTINCT
        COALESCE(property_type, 'unknown') AS property_type,
        CASE
            WHEN LOWER(COALESCE(property_type, '')) LIKE '%apartment%' THEN 'apartment'
            WHEN LOWER(COALESCE(property_type, '')) LIKE '%condo%' THEN 'condo'
            WHEN LOWER(COALESCE(property_type, '')) LIKE '%house%' THEN 'house'
            WHEN LOWER(COALESCE(property_type, '')) LIKE '%town%' THEN 'townhouse'
            WHEN LOWER(COALESCE(property_type, '')) LIKE '%basement%' THEN 'basement'
            WHEN LOWER(COALESCE(property_type, '')) LIKE '%room%' THEN 'room'
            WHEN LOWER(COALESCE(property_type, '')) LIKE '%garage%' THEN 'auxiliary'
            WHEN LOWER(COALESCE(property_type, '')) LIKE '%parking%' THEN 'auxiliary'
            WHEN LOWER(COALESCE(property_type, '')) LIKE '%storage%' THEN 'auxiliary'
            WHEN LOWER(COALESCE(property_type, '')) LIKE '%locker%' THEN 'auxiliary'
            ELSE 'other'
        END AS property_group,

        CASE
            WHEN LOWER(COALESCE(property_type, '')) LIKE '%garage%'
              OR LOWER(COALESCE(property_type, '')) LIKE '%parking%'
              OR LOWER(COALESCE(property_type, '')) LIKE '%storage%'
              OR LOWER(COALESCE(property_type, '')) LIKE '%locker%'
                THEN TRUE
            ELSE FALSE
        END AS is_auxiliary_listing
    FROM staging.stg_rental_listings
)

INSERT INTO warehouse.dim_property (
    property_type,
    property_group,
    is_auxiliary_listing
)
SELECT 
    property_type,
    property_group,
    is_auxiliary_listing
FROM property_source;

-- WRITE CTE FOR date, fact sheet and INSERT INTO statements for them