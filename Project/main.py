from pathlib import Path
from sqlalchemy import text
from Pipelines.Ingestion.rentals_ca_ingestion import run_ingestion
from Pipelines.Transform.load_to_postgre import create_db_engine, run_loader

def run_sql_script(engine, sql_path: Path):
    with open(sql_path, "r") as file:
        sql = file.read()

    with engine.begin() as conn:
        conn.execute(text(sql))

def main():
    base_dir = Path(__file__).resolve().parent
    engine = create_db_engine()

    run_ingestion()
    run_sql_script(engine, base_dir / "Pipelines" / "Transform" / "sql" / "00_create_schemas.sql")
    run_sql_script(engine, base_dir / "Pipelines" / "Transform" / "sql" / "01_create_raw_rentals.sql")
    run_loader()
    run_sql_script(engine, base_dir / "Pipelines" / "Transform" / "sql" / "02_create_staging_rentals.sql")

if __name__ == "__main__":
    main()