-- create_mart_rental_summary.sql
-- Purpose: create mart tables for analysis ready use
DROP TABLE IF EXISTS mart.rental_listing_enriched;
DROP TABLE IF EXISTS mart.rent_summary_by_property_location;

-- create the rental_listing_enriched table. This table joins the dimension and fact tables
-- produced in warehouse and is later used in producing aggregated tables for analysis use
CREATE TABLE mart.rental_listing_enriched AS
SELECT
    f.snapshot_key,
    dl.listing_id,
    dl.listing_name,
    dloc.street,
    dloc.postal_code,
    dloc.postal_fsa,
    dloc.longitude,
    dloc.latitude,
    dp.property_type,
    dp.property_group,
    dp.is_auxiliary_listing,
    f.date_key,
    dd.full_date,
    dd.year,
    dd.month,
    dd.quarter,
    f.rent_min,
    f.rent_max,
    f.rent_representative,
    f.rent_bound_type,
    f.beds_avg,
    f.bath_avg,
    f.size_avg,
    f.rent_per_bed,
    f.rent_per_sqft,
    f.images_count,
    f.loaded_at
FROM warehouse.fact_rental_listing_snapshot f
INNER JOIN warehouse.dim_listing dl  ON f.listing_key = dl.listing_key
INNER JOIN warehouse.dim_location dloc ON f.location_key = dloc.location_key
INNER JOIN warehouse.dim_property dp ON f.property_key = dp.property_key
INNER JOIN warehouse.dim_date dd ON f.date_key = dd.date_key;

-- create the rent_summary_by_property_location table, this table is the aggregated summary table
-- of property location ready for analysis use
CREATE TABLE mart.rent_summary_by_property_location AS
SELECT
    full_date,
    year,
    month,
    quarter,
    postal_fsa,
    property_group,
    COUNT(*) AS listing_count,
    AVG(rent_representative) AS avg_rent,
    MIN(rent_representative) AS min_rent,
    MAX(rent_representative) AS max_rent,
    AVG(beds_avg) AS avg_beds,
    AVG(bath_avg) AS avg_baths,
    AVG(size_avg) AS avg_size,
    AVG(rent_per_bed) AS avg_rent_per_bed,
    AVG(rent_per_sqft) AS avg_rent_per_sqft,
    COUNT(*) FILTER (
        WHERE size_avg IS NOT NULL
    ) AS listings_with_size,
    COUNT(*) FILTER (
        WHERE rent_per_sqft IS NOT NULL
    ) AS listings_with_rent_per_sqft,
    COUNT(*) FILTER (
        WHERE rent_bound_type = 'range'
    ) AS range_rent_count,
    COUNT(*) FILTER (
        WHERE rent_bound_type = 'upper_bound_only'
    ) AS upper_bound_only_count
FROM mart.rental_listing_enriched
WHERE rent_representative IS NOT NULL
GROUP BY
    full_date,
    year,
    month,
    quarter,
    postal_fsa,
    property_group
ORDER BY
    full_date,
    postal_fsa,
    property_group;