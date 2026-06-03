-- create_staging_rentals.sql
-- Purpose: clean and standardize the data from raw table

DROP TABLE IF EXISTS staging.stg_rental_listings;

CREATE TABLE staging.stg_rental_listings AS
SELECT 
    TRIM(name) AS listing_name,
    listing_id,
    TRIM(street) AS street,
    UPPER(REPLACE(TRIM(postal_code), ' ', '')) AS postal_code,
    longitude,
    latitude,
    rent_min,
    rent_max,
    beds_min,
    beds_max,
    bath_min,
    bath_max,
    size_min,
    size_max,
    created_date,
    modified_date,
    LOWER(TRIM(highlight_status)) AS highlight_status,
    images_count,
    LOWER(TRIM(property_type)) AS property_type,
    verified,
    loaded_at
FROM raw.rental_listings;

SELECT name AS listing_name FROM staging.stg_rental_listings LIMIT 20;