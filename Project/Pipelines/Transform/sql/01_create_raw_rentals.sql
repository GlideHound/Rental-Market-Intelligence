-- create_raw_rentals.sql
-- Purpose: create raw landing table for rental listing data

DROP TABLE IF EXISTS raw.rental_listings;

CREATE TABLE raw.rental_listings (
    name TEXT,
    listing_id TEXT PRIMARY KEY,
    city TEXT,
    province TEXT,
    street TEXT,
    postal_code TEXT,
    longitude DOUBLE PRECISION,
    latitude DOUBLE PRECISION,
    rent_min DOUBLE PRECISION, 
    rent_max DOUBLE PRECISION,
    beds_min DOUBLE PRECISION,
    beds_max DOUBLE PRECISION,
    bath_min DOUBLE PRECISION,
    bath_max DOUBLE PRECISION,
    size_min DOUBLE PRECISION,
    size_max DOUBLE PRECISION,
    created_date TIMESTAMP,
    modified_date TIMESTAMP,
    highlight_status TEXT,
    images_count INTEGER,
    property_type TEXT,
    verified BOOLEAN,
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);