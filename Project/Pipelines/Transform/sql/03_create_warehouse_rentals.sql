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
    city TEXT,
    province TEXT,
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

-- dim_listing CTE and insert statement
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

-- dim_location CTE and insert statement
WITH location_source AS (
    SELECT DISTINCT
        city,
        province,
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
    WHERE city IS NOT NULL
       OR province IS NOT NULL
       OR street IS NOT NULL
       OR postal_code IS NOT NULL
       OR longitude IS NOT NULL
       OR latitude IS NOT NULL
)

INSERT INTO warehouse.dim_location (
    city,
    province,
    street,
    postal_code,
    postal_fsa,
    longitude,
    latitude
)
SELECT
    city,
    province,
    street,
    postal_code,
    postal_fsa,
    longitude,
    latitude
FROM location_source;


-- dim_property CTE and insert statement
-- need to check in future after we scale the data ingestion phase
WITH property_source AS (
    SELECT DISTINCT
        COALESCE(property_type, 'unknown') AS property_type,
        CASE
            WHEN property_type IN ('house', 'single_family_home', 'main_floor')
                THEN 'house'
            WHEN property_type = 'apartment'
                THEN 'apartment'
            WHEN property_type IN ('condo', 'condo_community')
                THEN 'condo'
            WHEN property_type IN ('town_house', 'town_house_community')
                THEN 'townhouse'
            WHEN property_type IN ('duplex', 'triplex', 'fourplex', 'multi_unit')
                THEN 'multi_unit'
            WHEN property_type IN ('room', 'shared_room')
                THEN 'room'
            WHEN property_type IS NULL
                THEN 'unknown'
            ELSE 'other'
        END AS property_group,
        FALSE AS is_auxiliary_listing
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

-- dim_date CTE and insert statement
WITH date_source AS (
    SELECT DISTINCT
        loaded_at::date AS full_date
    FROM staging.stg_rental_listings
    WHERE loaded_at IS NOT NULL
)

INSERT INTO warehouse.dim_date (
    date_key,
    full_date,
    year,
    month,
    day,
    quarter,
    month_name,
    day_of_week
)
SELECT
    TO_CHAR(full_date, 'YYYYMMDD')::INTEGER AS date_key,
    full_date,
    EXTRACT(YEAR FROM full_date)::INTEGER AS year,
    EXTRACT(MONTH FROM full_date)::INTEGER AS month,
    EXTRACT(DAY FROM full_date)::INTEGER AS day,
    EXTRACT(QUARTER FROM full_date)::INTEGER AS quarter,
    TRIM(TO_CHAR(full_date, 'Month')) AS month_name,
    TRIM(TO_CHAR(full_date, 'Day')) AS day_of_week
FROM date_source;

-- fact_rental_listing_snapshot CTE and insert statement
-- further checking of rent_min to rent_max needed
WITH fact_source AS (
    SELECT 
        dl.listing_key,
        dloc.location_key,
        dp.property_key,
        dd.date_key,
        s.rent_min_clean,
        s.rent_max_clean,
        s.rent_avg,
        s.rent_bound_type,
        s.beds_avg,
        s.bath_avg,
        s.size_avg,
        s.images_count,
        s.loaded_at
    FROM staging.stg_rental_listings s
    LEFT JOIN warehouse.dim_listing dl ON s.listing_id = dl.listing_id
    LEFT JOIN warehouse.dim_location dloc ON s.city IS NOT DISTINCT FROM dloc.city
        AND s.province IS NOT DISTINCT FROM dloc.province
        AND s.street IS NOT DISTINCT FROM dloc.street
        AND s.postal_code IS NOT DISTINCT FROM dloc.postal_code
        AND s.longitude IS NOT DISTINCT FROM dloc.longitude
        AND s.latitude IS NOT DISTINCT FROM dloc.latitude
    LEFT JOIN warehouse.dim_property dp ON COALESCE(s.property_type, 'unknown') = dp.property_type
    LEFT JOIN warehouse.dim_date dd ON s.loaded_at::date = dd.full_date
    WHERE s.has_rent = TRUE
      AND s.invalid_rent_range = FALSE
      AND s.invalid_beds_range = FALSE
      AND s.invalid_bath_range = FALSE
      AND s.invalid_size_range = FALSE
)

INSERT INTO warehouse.fact_rental_listing_snapshot (
    listing_key,
    location_key,
    property_key,
    date_key,
    rent_min,
    rent_max,
    rent_representative,
    rent_bound_type,
    beds_avg,
    bath_avg,
    size_avg,
    rent_per_bed,
    rent_per_sqft,
    images_count,
    loaded_at
)
SELECT
    listing_key,
    location_key,
    property_key,
    date_key,
    rent_min_clean AS rent_min,
    rent_max_clean AS rent_max,
    rent_avg AS rent_representative,
    rent_bound_type,
    beds_avg,
    bath_avg,
    size_avg,
    CASE
        WHEN beds_avg IS NOT NULL AND beds_avg > 0
            THEN rent_avg / beds_avg
        ELSE NULL
    END AS rent_per_bed,
    CASE
        WHEN size_avg IS NOT NULL AND size_avg > 0
            THEN rent_avg / size_avg
        ELSE NULL
    END AS rent_per_sqft,
    images_count,
    loaded_at
FROM fact_source
WHERE listing_key IS NOT NULL
  AND location_key IS NOT NULL
  AND property_key IS NOT NULL
  AND date_key IS NOT NULL;