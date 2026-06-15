-- create_warehouse_rentals.sql
-- Purpose: partition out fact tables from the staging table
DROP TABLE IF EXISTS warehouse.dim_listing;

CREATE TABLE warehouse.dim_listing (
    listing_key SERIAL PRIMARY KEY,
    listing_name TEXT,
    listing_id TEXT NOT NULL UNIQUE,
    street TEXT,
    created_date TIMESTAMP,
    modified_date TIMESTAMP,
    verified BOOLEAN
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
    street,
    created_date,
    modified_date,
    verified
)
SELECT
    listing_id,
    listing_name,
    street,
    created_date,
    modified_date,
    verified
FROM latest_listing
WHERE rn = 1;

-- CREATE TABLE warehouse.dim_location
-- CREATE TABLE warehouse.dim_property
-- CREATE TABLE warehouse.dim_date
-- CREATE TABLE warehouse.fact_rental_listing_snapshot