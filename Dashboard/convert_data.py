import pandas as pd
import geopandas as gpd
import os
import config

def bake_to_parquet():
    print("Reading Shapefile...")
    # Using config to grab the raw shapefile directly from the Datasets folder
    gdf = gpd.read_file(config.LSOA_SHAPEFILE)[["LSOA21CD", "LSOA21NM", "geometry"]]

    print("Setting original British National Grid CRS...")
    gdf.set_crs(epsg=27700, inplace=True, allow_override=True)

    print("Reprojecting to standard web coordinates...")
    gdf = gdf.to_crs(epsg=4326)

    print("Saving to lightweight GeoParquet...")
    # Using config to drop the finished file straight into the Dashboard folder
    gdf.to_parquet(config.LSOA_BOUNDARIES_PARQUET)
    print("Shapefile successfully converted.")

    # Forecast
    pd.read_csv(config.SUMMER_FORECAST_CSV).to_parquet(config.SUMMER_FORECAST_PARQUET)
    print("Forecast converted.")

    # Z-Scores
    months = ["04", "05", "06", "07", "08"]
    for month in months:
        # Grab the CSV from the forecast results directory
        z_csv_path = os.path.join(config.FORECAST_RESULTS_DIR, f"z_scores_2026_{month}.csv")
        # Save the Parquet file directly into the Dashboard directory
        z_parquet_path = os.path.join(config.DASHBOARD_DIR, f"z_scores_2026_{month}.parquet")

        if os.path.exists(z_csv_path):
            pd.read_csv(z_csv_path).to_parquet(z_parquet_path)
            print(f"Successfully converted z_scores_2026_{month}.parquet")
        else:
            print(f"Warning: Could not find {z_csv_path}")

    # Time Series (Prophet Input)
    pd.read_csv(config.PROPHET_INPUT_CSV).to_parquet(config.PROPHET_INPUT_PARQUET)
    print("Time Series converted.")

    # Crime Types
    pd.read_csv(config.CRIME_TYPES_CSV).to_parquet(config.CRIME_TYPES_PARQUET)
    print("Crime Types converted.")

    # CCTV Priority
    pd.read_csv(config.CCTV_PRIORITY_CSV).to_parquet(config.CCTV_PRIORITY_PARQUET)
    print("CCTV Priority converted.")

    print("All files successfully converted to Parquet and ready for the Dashboard!")

if __name__ == "__main__":
    bake_to_parquet()