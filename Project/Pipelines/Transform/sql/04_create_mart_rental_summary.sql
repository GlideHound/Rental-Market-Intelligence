-- create_mart_rental_summary.sql
-- Purpose: create mart tables for analysis ready use
DROP TABLE IF EXISTS mart.rental_listing_enriched;
DROP TABLE IF EXISTS mart.rent_summary_by_property_location

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

