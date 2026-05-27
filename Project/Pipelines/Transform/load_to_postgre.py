from pathlib import Path
from sqlalchemy import create_engine
import pandas as pd

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
    username = "username"
    database = "database name"

    connection_url = f"postgresql+psycopg2://{username}@localhost:5432/{database}"

    engine = create_engine(connection_url)
    return engine

# Name: main()
# Purpose: The driver function
# Parameters: None
# Returns: None
def main():
    base_dir = Path(__file__).resolve().parents[2]
    file_path_parquet = base_dir / "Data" / "Raw" / "toronto_rentals.parquet"

    df_raw = read_raw_parquet(file_path_parquet)

    return None

if __name__ == "__main__":
    main()