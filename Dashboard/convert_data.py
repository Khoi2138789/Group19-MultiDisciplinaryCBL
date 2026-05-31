import pandas as pd
import geopandas as gpd
import os

def bake_to_parquet():
    # 1. Convert the Shapefile to GeoParquet (NO SIMPLIFICATION NEEDED)
    shapefile_path = r"C:\Users\20241114\PycharmProjects\PythonProject\Datasets\Lower_layer_Super_Output_Areas_December_2021_Boundaries_EW_BFC_V10_-7599572456947714539\LSOA_2021_EW_BFC_V10.shp"

    print("Reading Shapefile...")
    gdf = gpd.read_file(shapefile_path)[['LSOA21CD', 'LSOA21NM', 'geometry']]

    print("Setting original British National Grid CRS...")
    gdf.set_crs(epsg=27700, inplace=True, allow_override=True)

    print("Reprojecting to standard web coordinates...")
    gdf = gdf.to_crs(epsg=4326)


    print("Saving to lightweight GeoParquet...")
    gdf.to_parquet("lsoas_boundaries.parquet")
    print("Shapefile successfully converted.")

    forecast_path = r"C:\Users\20241114\PycharmProjects\PythonProject\Prophet Forecasting\Forecasting Results\summer_2026_forecast.csv"
    pd.read_csv(forecast_path).to_parquet("summer_2026_forecast.parquet")
    print("Forecast converted.")

    results_folder = r"C:\Users\20241114\PycharmProjects\PythonProject\Prophet Forecasting\Forecasting Results"
    months = ['04', '05', '06', '07', '08']
    for month in months:
        z_csv_path = os.path.join(results_folder, f"z_scores_2026_{month}.csv")
        z_parquet_name = f"z_scores_2026_{month}.parquet"

        if os.path.exists(z_csv_path):
            pd.read_csv(z_csv_path).to_parquet(z_parquet_name)
            print(f"  -> Successfully converted {z_parquet_name}")
        else:
            print(f"  -> Warning: Could not find {z_csv_path}")

    time_path = r"C:\Users\20241114\PycharmProjects\PythonProject\Prophet Forecasting\Training Data\prophet_input.csv"
    pd.read_csv(time_path).to_parquet("prophet_input.parquet")
    print("Time Series converted.")

    # 4. Convert the Crime Types CSV
    types_path = r"C:\Users\20241114\PycharmProjects\PythonProject\DuckDB\pcp_crime_types.csv"
    pd.read_csv(types_path).to_parquet("pcp_crime_types.parquet")
    print("Crime Types converted.")

    print("All files successfully converted to Parquet!")


if __name__ == "__main__":
    bake_to_parquet()