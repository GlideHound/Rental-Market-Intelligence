-- create_staging_rentals.sql
-- Purpose: clean and standardize the data from raw table
-- We already handled deduplication of listing_id in API call phase, so don't worry about that

-- In the future, check edge case values like rent price = 1
DROP TABLE IF EXISTS staging.stg_rental_listings;

-- create_staging_rentals.sql
-- Purpose: clean and standardize the data from raw table
-- We already handled deduplication of listing_id in API call phase, so don't worry about that

DROP TABLE IF EXISTS staging.stg_rental_listings;

CREATE TABLE staging.stg_rental_listings AS
WITH cleaned AS (
    SELECT 
        TRIM(name) AS listing_name,
        listing_id,
        NULLIF(TRIM(street), '') AS street,
        UPPER(REPLACE(TRIM(postal_code), ' ', '')) AS postal_code,
        longitude,
        latitude,
        rent_min,
        rent_max,
        CASE
            WHEN rent_min = 1 THEN NULL
            ELSE rent_min
        END AS rent_min_clean,
        CASE
            WHEN rent_max = 1 THEN NULL
            ELSE rent_max
        END AS rent_max_clean,
        beds_min,
        beds_max,
        bath_min,
        bath_max,
        size_min,
        size_max,
        created_date,
        modified_date,
        LOWER(NULLIF(TRIM(highlight_status), '')) AS highlight_status,
        images_count,
        LOWER(NULLIF(TRIM(property_type), '')) AS property_type,
        verified,
        loaded_at
    FROM raw.rental_listings
    WHERE listing_id IS NOT NULL 
      AND name IS NOT NULL
      AND TRIM(name) <> ''
      AND (rent_min IS NOT NULL OR rent_max IS NOT NULL)
)

SELECT 
    listing_name,
    listing_id,
    street,
    postal_code,
    longitude,
    latitude,
    rent_min,
    rent_max,
    rent_min_clean,
    rent_max_clean,
    CASE
        WHEN rent_min = 1 AND rent_max_clean IS NOT NULL
            THEN rent_max_clean
        WHEN rent_min_clean IS NOT NULL 
         AND rent_max_clean IS NOT NULL 
         AND rent_min_clean <= rent_max_clean
            THEN (rent_min_clean + rent_max_clean) / 2.0
        WHEN rent_min_clean IS NOT NULL
            THEN rent_min_clean
        WHEN rent_max_clean IS NOT NULL
            THEN rent_max_clean
        ELSE NULL
    END AS rent_avg,
    CASE
        WHEN rent_min = 1 AND rent_max_clean IS NOT NULL
            THEN 'upper_bound_only'
        WHEN rent_min_clean IS NOT NULL 
         AND rent_max_clean IS NOT NULL 
         AND rent_min_clean <= rent_max_clean
            THEN 'range'
        WHEN rent_min_clean IS NOT NULL 
         AND rent_max_clean IS NULL
            THEN 'lower_bound_only'
        WHEN rent_min_clean IS NULL 
         AND rent_max_clean IS NOT NULL
            THEN 'upper_bound_only'
        ELSE 'unknown'
    END AS rent_bound_type,
    CASE
        WHEN rent_min = 1 THEN TRUE
        ELSE FALSE
    END AS rent_min_placeholder_flag,
    CASE
        WHEN rent_max = 1 THEN TRUE
        ELSE FALSE
    END AS rent_max_placeholder_flag,
    CASE
        WHEN rent_min_clean IS NOT NULL
         AND rent_max_clean IS NOT NULL
         AND rent_min_clean > rent_max_clean
            THEN TRUE
        ELSE FALSE
    END AS invalid_rent_range,
    beds_min,
    beds_max,
    CASE 
        WHEN beds_min IS NOT NULL AND beds_max IS NOT NULL THEN (beds_min + beds_max) / 2.0
        WHEN beds_min IS NOT NULL THEN beds_min
        WHEN beds_max IS NOT NULL THEN beds_max
        ELSE NULL
    END AS beds_avg,
    bath_min,
    bath_max,
    CASE 
        WHEN bath_min IS NOT NULL AND bath_max IS NOT NULL THEN (bath_min + bath_max) / 2.0
        WHEN bath_min IS NOT NULL THEN bath_min
        WHEN bath_max IS NOT NULL THEN bath_max
        ELSE NULL
    END AS bath_avg,
    size_min,
    size_max,
    CASE
        WHEN size_min IS NOT NULL AND size_max IS NOT NULL THEN (size_min + size_max) / 2.0
        WHEN size_min IS NOT NULL THEN size_min
        WHEN size_max IS NOT NULL THEN size_max
        ELSE NULL
    END AS size_avg,
    created_date,
    modified_date,
    highlight_status,
    images_count,
    property_type,
    verified,
    loaded_at,
    (rent_min_clean IS NOT NULL OR rent_max_clean IS NOT NULL) AS has_rent,
    (size_min IS NOT NULL OR size_max IS NOT NULL) AS has_size,
    (longitude IS NOT NULL AND latitude IS NOT NULL) AS has_location,
    (beds_min IS NOT NULL OR beds_max IS NOT NULL) AS has_beds,
    (bath_min IS NOT NULL OR bath_max IS NOT NULL) AS has_baths
FROM cleaned
WHERE rent_min_clean IS NOT NULL 
   OR rent_max_clean IS NOT NULL;