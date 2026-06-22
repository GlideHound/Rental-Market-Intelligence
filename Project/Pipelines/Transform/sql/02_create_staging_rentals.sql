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
        CASE
            WHEN beds_min >= 0 THEN beds_min
            ELSE NULL
        END AS beds_min_clean,

        CASE
            WHEN beds_max >= 0 THEN beds_max
            ELSE NULL
        END AS beds_max_clean,

        bath_min,
        bath_max,
        CASE
            WHEN bath_min >= 0 THEN bath_min
            ELSE NULL
        END AS bath_min_clean,
        CASE
            WHEN bath_max >= 0 THEN bath_max
            ELSE NULL
        END AS bath_max_clean,

        size_min,
        size_max,
        CASE
            WHEN size_min > 0 THEN size_min
            ELSE NULL
        END AS size_min_clean,

        CASE
            WHEN size_max > 0 THEN size_max
            ELSE NULL
        END AS size_max_clean,

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
        WHEN rent_min = 1 AND rent_max_clean IS NOT NULL THEN rent_max_clean
        WHEN rent_min_clean IS NOT NULL
        AND rent_max_clean IS NOT NULL
        AND rent_min_clean > rent_max_clean THEN NULL
        WHEN rent_min_clean IS NOT NULL 
        AND rent_max_clean IS NOT NULL 
        AND rent_min_clean <= rent_max_clean THEN (rent_min_clean + rent_max_clean) / 2.0
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
    beds_min_clean,
    beds_max_clean,
    CASE 
        WHEN beds_min_clean IS NOT NULL 
        AND beds_max_clean IS NOT NULL 
        AND beds_min_clean > beds_max_clean THEN NULL
        WHEN beds_min_clean IS NOT NULL 
        AND beds_max_clean IS NOT NULL 
        AND beds_min_clean <= beds_max_clean
        THEN (beds_min_clean + beds_max_clean) / 2.0
        WHEN beds_min_clean IS NOT NULL THEN beds_min_clean
        WHEN beds_max_clean IS NOT NULL THEN beds_max_clean
        ELSE NULL
    END AS beds_avg,

    CASE
        WHEN beds_min_clean IS NOT NULL
        AND beds_max_clean IS NOT NULL
        AND beds_min_clean > beds_max_clean THEN TRUE
        ELSE FALSE
    END AS invalid_beds_range,
    bath_min,
    bath_max,
    bath_min_clean,
    bath_max_clean,
    CASE 
        WHEN bath_min_clean IS NOT NULL 
        AND bath_max_clean IS NOT NULL 
        AND bath_min_clean > bath_max_clean THEN NULL
        WHEN bath_min_clean IS NOT NULL 
        AND bath_max_clean IS NOT NULL 
        AND bath_min_clean <= bath_max_clean THEN (bath_min_clean + bath_max_clean) / 2.0
        WHEN bath_min_clean IS NOT NULL THEN bath_min_clean
        WHEN bath_max_clean IS NOT NULL THEN bath_max_clean
        ELSE NULL
    END AS bath_avg,
    
    CASE
        WHEN bath_min_clean IS NOT NULL
        AND bath_max_clean IS NOT NULL
        AND bath_min_clean > bath_max_clean THEN TRUE
        ELSE FALSE
    END AS invalid_bath_range,

    size_min,
    size_max,
    size_min_clean,
    size_max_clean,
    CASE
        WHEN size_min_clean IS NOT NULL 
        AND size_max_clean IS NOT NULL
        AND size_min_clean > size_max_clean THEN NULL
        WHEN size_min_clean IS NOT NULL 
        AND size_max_clean IS NOT NULL
        AND size_min_clean <= size_max_clean THEN (size_min_clean + size_max_clean) / 2.0
        WHEN size_min_clean IS NOT NULL THEN size_min_clean
        WHEN size_max_clean IS NOT NULL THEN size_max_clean
        ELSE NULL
    END AS size_avg,

    CASE
        WHEN size_min_clean IS NOT NULL 
        AND size_max_clean IS NOT NULL
        AND size_min_clean > size_max_clean THEN TRUE
        ELSE FALSE
    END AS invalid_size_range,

    created_date,
    modified_date,
    highlight_status,
    images_count,
    property_type,
    verified,
    loaded_at,
    (rent_min_clean IS NOT NULL OR rent_max_clean IS NOT NULL) AS has_rent,
    (longitude IS NOT NULL AND latitude IS NOT NULL) AS has_location,
    (size_min_clean IS NOT NULL OR size_max_clean IS NOT NULL) AS has_size,
    (beds_min_clean IS NOT NULL OR beds_max_clean IS NOT NULL) AS has_beds,
    (bath_min_clean IS NOT NULL OR bath_max_clean IS NOT NULL) AS has_baths
FROM cleaned
WHERE rent_min_clean IS NOT NULL 
   OR rent_max_clean IS NOT NULL;