-- create_staging_rentals.sql
-- Purpose: clean and standardize the data from raw table
-- We already handled deduplication of listing_id in API call phase, so don't worry about that

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
    CASE 
        WHEN rent_min IS NOT NULL AND rent_max IS NOT NULL THEN (rent_min + rent_max) / 2
        WHEN rent_min IS NOT NULL THEN rent_min
        WHEN rent_max IS NOT NULL THEN rent_max
        ELSE NULL
    END AS rent_avg,
    beds_min,
    beds_max,
    CASE 
        WHEN beds_min IS NOT NULL AND beds_max IS NOT NULL THEN (beds_min + beds_max) / 2
        WHEN beds_min IS NOT NULL THEN beds_min
        WHEN beds_max IS NOT NULL THEN beds_max
        ELSE NULL
    END AS beds_avg,
    bath_min,
    bath_max,
    CASE 
        WHEN bath_min IS NOT NULL AND bath_max IS NOT NULL THEN (bath_min + bath_max) / 2
        WHEN bath_min IS NOT NULL THEN bath_min
        WHEN bath_max IS NOT NULL THEN bath_max
        ELSE NULL
    END AS bath_avg,
    size_min,
    size_max,
    CASE
        WHEN size_min IS NOT NULL AND size_max IS NOT NULL THEN (size_min + size_max) / 2
        WHEN size_min IS NOT NULL THEN size_min
        WHEN size_max IS NOT NULL THEN size_max
        ELSE NULL
    END AS size_avg,
    created_date,
    modified_date,
    LOWER(TRIM(highlight_status)) AS highlight_status,
    images_count,
    LOWER(TRIM(property_type)) AS property_type,
    verified,
    loaded_at,
    (rent_min IS NOT NULL OR rent_max IS NOT NULL) AS has_rent,
    (size_min IS NOT NULL OR size_max IS NOT NULL) AS has_size,
    (longitude IS NOT NULL AND latitude IS NOT NULL) AS has_location,
    (beds_min IS NOT NULL OR beds_max IS NOT NULL) AS has_beds,
    (bath_min IS NOT NULL OR bath_max IS NOT NULL) AS has_baths
FROM raw.rental_listings
WHERE listing_id IS NOT NULL 
    AND name IS NOT NULL
    AND TRIM(name) <> ''
    AND (rent_min IS NOT NULL OR rent_max IS NOT NULL);

SELECT listing_name FROM staging.stg_rental_listings LIMIT 20;