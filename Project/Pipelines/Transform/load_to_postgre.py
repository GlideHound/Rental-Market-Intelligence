import pandas as pd
import os
from dotenv import load_dotenv
from pathlib import Path
from sqlalchemy import create_engine

# Name: read_raw_parquet()
# Purpose: read_raw_parquet() reads in the parquet file that contains the raw rental listings
# Parameters: file_path_parquet (Path): This is the file path for the raw parquet file that contains
#                                       the raw rental listings
# Returns: A pandas dataframe
def read_raw_parquet(file_path_parquet: Path):
    df = pd.read_parquet(file_path_parquet)

    return df

# Name: create_db_engine()
# Purpose: create_db_engine() establishes connection with the PostgreSQL database
# Parameters: None
# Returns: the connection
def create_db_engine():
    load_dotenv()

    username = os.getenv("POSTGRES_USER")
    database = os.getenv("POSTGRES_DB")
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT")

    connection_url = f"postgresql+psycopg2://{username}@{host}:{port}/{database}"

    engine = create_engine(connection_url)
    return engine

# Name: 
# Purpose: 
# Parameters: 
# Returns: 
def load_df_to_postgre(df: pd.DataFrame, engine):
    df.to_sql(
        name = "rental_listings",
        con = engine,
        schema = "raw",
        if_exists = "append",
        index = False
    )

    print(f"Loaded {len(df)} rows into raw.rental_listings")

    return None

# Name: run_loader()
# Purpose: run_loader() wires up everything in load_to_postgre.py and serves as the purpose of
#          the main function
# Parameters: None
# Returns: None
def run_loader():
    base_dir = Path(__file__).resolve().parents[2]
    file_path_parquet = base_dir / "Data" / "Raw" / "toronto_rentals.parquet"

    df_raw = read_raw_parquet(file_path_parquet)
    engine = create_db_engine()
    load_df_to_postgre(df_raw, engine)

    return None

# Name: main()
# Purpose: The driver function
# Parameters: None
# Returns: None
def main():
    run_loader()

if __name__ == "__main__":
    df_raw = main()