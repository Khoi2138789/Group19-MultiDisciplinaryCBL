import pandas as pd
import geopandas as gpd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def bake_to_parquet():

    gdf = gpd.read_file(config.LSOA_SHAPEFILE)[["LSOA21CD", "LSOA21NM", "geometry"]]

    gdf.set_crs(epsg=27700, inplace=True, allow_override=True)

    gdf = gdf.to_crs(epsg=4326)

    gdf.to_parquet(config.LSOA_BOUNDARIES_PARQUET)


    pd.read_csv(config.SUMMER_FORECAST_CSV).to_parquet(config.SUMMER_FORECAST_PARQUET)

    months = ["04", "05", "06", "07", "08"]
    for month in months:
        z_csv_path = os.path.join(config.FORECAST_RESULTS_DIR, f"z_scores_2026_{month}.csv")
        z_parquet_path = os.path.join(config.DASHBOARD_DIR, f"z_scores_2026_{month}.parquet")

        if os.path.exists(z_csv_path):
            pd.read_csv(z_csv_path).to_parquet(z_parquet_path)
            print(f"Successfully converted z_scores_2026_{month}.parquet")
        else:
            print(f"Warning: Could not find {z_csv_path}")

    pd.read_csv(config.PROPHET_INPUT_CSV).to_parquet(config.PROPHET_INPUT_PARQUET)


    pd.read_csv(config.CRIME_TYPES_CSV).to_parquet(config.CRIME_TYPES_PARQUET)

    pd.read_csv(config.CCTV_PRIORITY_CSV).to_parquet(config.CCTV_PRIORITY_PARQUET)
    print("All CSV files have been successfully converted to Parquet format.")

if __name__ == "__main__":
    bake_to_parquet()