import os
import duckdb
from dotenv import load_dotenv
from pathlib import Path
from sqlalchemy import create_engine


# Name: create_db_engine()
# Purpose: create_db_engine() establishes connection with the PostgreSQL database
# Parameters: None
# Returns: the SQLAlchemy engine
def create_db_engine():
    load_dotenv()

    username = os.getenv("POSTGRES_USER")
    database = os.getenv("POSTGRES_DB")
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT")

    connection_url = f"postgresql+psycopg2://{username}@{host}:{port}/{database}"

    engine = create_engine(connection_url)
    return engine


# Name: build_postgres_attach_string()
# Purpose: build a PostgreSQL connection string for DuckDB's postgres extension
# Parameters: None
# Returns: PostgreSQL connection string
def build_postgres_attach_string():
    load_dotenv()

    username = os.getenv("POSTGRES_USER")
    database = os.getenv("POSTGRES_DB")
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT")
    
    postgres_conn = (
        f"host={host} "
        f"port={port} "
        f"dbname={database} "
        f"user={username}"
    )

    return postgres_conn


# Name: load_parquet_to_postgre_with_duckdb()
# Purpose: load raw parquet data directly into PostgreSQL using DuckDB
# Parameters: file_path_parquet (Path): path to raw parquet file
# Returns: None
def load_parquet_to_postgre_with_duckdb(file_path_parquet: Path):
    postgres_conn = build_postgres_attach_string()

    parquet_path = file_path_parquet.as_posix()

    con = duckdb.connect()

    try:
        # Install/load DuckDB PostgreSQL extension
        con.execute("INSTALL postgres;")
        con.execute("LOAD postgres;")

        # Attach PostgreSQL database to DuckDB
        con.execute(f"""
            ATTACH '{postgres_conn}' AS pg_db (TYPE postgres);
        """)

        # Optional: clear raw table before loading
        # This is safe if your pipeline recreates/reloads raw data each run.
        con.execute("""
            DELETE FROM pg_db.raw.rental_listings;
        """)

        # Load Parquet directly into PostgreSQL.
        # Explicit column list is safer than SELECT *.
        con.execute(f"""
            INSERT INTO pg_db.raw.rental_listings (
                name,
                listing_id,
                city,
                province,
                street,
                postal_code,
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
                highlight_status,
                images_count,
                property_type,
                verified
            )
            SELECT
                name,
                listing_id,
                city,
                province,
                street,
                postal_code,
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
                highlight_status,
                images_count,
                property_type,
                verified
            FROM read_parquet('{parquet_path}');
        """)

        loaded_count = con.execute("""
            SELECT COUNT(*)
            FROM pg_db.raw.rental_listings;
        """).fetchone()[0]

        print(f"Loaded {loaded_count} rows into raw.rental_listings using DuckDB")

    finally:
        con.close()

    return None


# Name: run_loader()
# Purpose: run_loader() wires up everything in load_to_postgre.py
# Parameters: None
# Returns: None
def run_loader():
    base_dir = Path(__file__).resolve().parents[2]
    file_path_parquet = base_dir / "Data" / "Raw" / "rentals_ca_listings.parquet"

    load_parquet_to_postgre_with_duckdb(file_path_parquet)

    return None


# Name: main()
# Purpose: The driver function
# Parameters: None
# Returns: None
def main():
    run_loader()


if __name__ == "__main__":
    main()