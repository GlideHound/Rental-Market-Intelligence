import yaml
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
    config_path = base_dir / "config.yml"

    with open(config_path, "r") as file:
        config = yaml.safe_load(file)

    engine = create_db_engine()

    run_ingestion(config)
    run_sql_script(engine, base_dir / "Pipelines" / "Transform" / "sql" / "00_create_schemas.sql")
    run_sql_script(engine, base_dir / "Pipelines" / "Transform" / "sql" / "01_create_raw_rentals.sql")
    run_loader()
    run_sql_script(engine, base_dir / "Pipelines" / "Transform" / "sql" / "02_create_staging_rentals.sql")
    run_sql_script(engine, base_dir / "Pipelines" / "Transform" / "sql" / "03_create_warehouse_rentals.sql")
    run_sql_script(engine, base_dir / "Pipelines" / "Transform" / "sql" / "04_create_mart_rental_summary.sql")
if __name__ == "__main__":
    main()