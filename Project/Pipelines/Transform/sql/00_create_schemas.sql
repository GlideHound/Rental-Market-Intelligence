-- create_schemas.sql
-- Purpose: create raw and cleaned schemas in the PostgreSql database

--raw: the raw data
--staging: cleaned and standardized data
--warehouse: business model fact tables
--mart: for analytical use

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS warehouse;
CREATE SCHEMA IF NOT EXISTS mart;