import pandas as pd
import geopandas as gpd
import os
import json
import config

# --- 1. GLOBAL CONFIGURATION PATHS ---
SHAPEFILE_PATH = config.LSOA_BOUNDARIES_PARQUET
FORECAST_PATH = config.SUMMER_FORECAST_PARQUET
HISTORICAL_TIME_SERIES_PATH = config.PROPHET_INPUT_PARQUET
HISTORICAL_CRIME_TYPES_PATH = config.CRIME_TYPES_PARQUET
CCTV_PRIORITY_PATH = config.CCTV_PRIORITY_PARQUET

Z_SCORE_MONTHS = ['04', '05', '06', '07', '08']


def load_and_prepare_data():
    """
    Centralized Data Engine Warehouse.
    Loads, filters, pivots, and joins multi-core forecasting
    and spatial datasets into memory for immediate dashboard consumption.
    """
    print("Initializing Dashboard Data Engine...")

    assets_dir = config.DASHBOARD_ASSETS_DIR
    os.makedirs(assets_dir, exist_ok=True)
    geojson_path = os.path.join(assets_dir, 'lsoas.json')
    needs_recalc = not os.path.exists(geojson_path)

    # --- 2. LOAD & FILTER GEOGRAPHY (ENGLAND ONLY) ---
    if needs_recalc:
        print("First-time setup: Loading GeoParquet boundaries with geometry...")
        gdf_map = gpd.read_parquet(SHAPEFILE_PATH)
    else:
        print("High-res map found! Loading lightweight Parquet boundaries...")
        gdf_map = pd.read_parquet(SHAPEFILE_PATH, columns=['LSOA21CD', 'LSOA21NM'])

    gdf_map = gdf_map.rename(columns={'LSOA21CD': 'LSOA_ID', 'LSOA21NM': 'LSOA_NAME'})

    # Structural Country Pruning: Filter to retain England 'E' LSOAs only
    print("Filtering spatial boundaries to England only...")
    gdf_map = gdf_map[gdf_map['LSOA_ID'].str.startswith('E', na=False)]

    # --- 3. LOAD & PIVOT HISTORICAL CRIME TYPES ---
    print("Pivoting Crime Type profiles...")
    df_types = pd.read_parquet(HISTORICAL_CRIME_TYPES_PATH)
    df_pcp_types = df_types.pivot(index='LSOA_ID', columns='Crime_Type', values='Total_Intensity').fillna(
        0).reset_index()
    crime_axes = [col for col in df_pcp_types.columns if col != 'LSOA_ID']

    # --- 4. LOAD & PIVOT HISTORICAL MOMENTUM TRENDS ---
    print("Pivoting Temporal Momentum profiles...")
    df_time = pd.read_parquet(HISTORICAL_TIME_SERIES_PATH)
    df_time['Month'] = pd.to_datetime(df_time['Month'])
    df_time['Year'] = df_time['Month'].dt.year

    df_time_pcp = df_time[df_time['Year'] <= 2025]
    df_yearly = df_time_pcp.groupby(['LSOA_ID', 'Year'])['Total_CII_Score'].mean().reset_index()
    df_pcp_momentum = df_yearly.pivot(index='LSOA_ID', columns='Year', values='Total_CII_Score').fillna(0).reset_index()

    # Normalize column headers to strings for seamless JSON compatibility
    df_pcp_momentum.columns = [str(col) if isinstance(col, int) else col for col in df_pcp_momentum.columns]
    momentum_axes = [col for col in df_pcp_momentum.columns if col != 'LSOA_ID']

    # --- 5. LOAD PROPHET SUMMER FORECASTS ---
    print("Loading Summer Predictions...")
    df_forecast = pd.read_parquet(FORECAST_PATH)
    df_forecast['ds'] = pd.to_datetime(df_forecast['ds'])

    # Clip lower bounds to eliminate unphysical negative intensity boundaries
    df_forecast['yhat'] = df_forecast['yhat'].clip(lower=0)
    df_forecast['yhat_lower'] = df_forecast['yhat_lower'].clip(lower=0)
    df_forecast['yhat_upper'] = df_forecast['yhat_upper'].clip(lower=0)

    # --- 6. MERGE INTER-CONNECTED SPATIAL RELATIONSHIPS ---
    print("Merging Spatial Master Dataset...")
    gdf_master = gdf_map.merge(df_pcp_types, on='LSOA_ID', how='left')
    gdf_master = gdf_master.merge(df_pcp_momentum, on='LSOA_ID', how='left')

    # Defensive Integration Layer: CCTV Priorities
    print("Loading CCTV Priority Rankings...")
    if os.path.exists(CCTV_PRIORITY_PATH):
        df_cctv = pd.read_parquet(CCTV_PRIORITY_PATH)
        df_cctv["LSOA_ID"] = df_cctv["LSOA_ID"].astype(str)

        cctv_cols = ["LSOA_ID", "unsolved_non_severe", "total_non_severe", "priority_level", "cctv_score", "cctv_rank"]
        gdf_master = gdf_master.merge(df_cctv[cctv_cols], on="LSOA_ID", how="left")

        for col in ["unsolved_non_severe", "total_non_severe", "priority_level", "cctv_score", "cctv_rank"]:
            gdf_master[col] = gdf_master[col].fillna(0)
        print("  -> CCTV priority metrics integrated smoothly.")
    else:
        print("  -> Warning: cctv_priority.parquet not detected. Injecting defensive zero-fallbacks.")
        gdf_master["unsolved_non_severe"] = 0
        gdf_master["total_non_severe"] = 0
        gdf_master["priority_level"] = 0
        gdf_master["cctv_score"] = 0
        gdf_master["cctv_rank"] = 0

    # Aggregate tactical metrics
    forecast_agg = df_forecast.groupby('LSOA_ID')[['yhat', 'yhat_lower', 'yhat_upper']].mean().reset_index()
    forecast_agg['yhat'] = forecast_agg['yhat'].clip(lower=0)
    forecast_agg['yhat_lower'] = forecast_agg['yhat_lower'].clip(lower=0)
    forecast_agg['yhat_upper'] = forecast_agg['yhat_upper'].clip(lower=0)

    forecast_agg['LSOA_ID'] = forecast_agg['LSOA_ID'].astype(str)
    gdf_master = gdf_master.merge(forecast_agg, on='LSOA_ID', how='left')

    # Secure downstream calculation safety via structural zero fillings
    for col in ['yhat', 'yhat_lower', 'yhat_upper']:
        if col in gdf_master.columns:
            gdf_master[col] = gdf_master[col].fillna(0)

    for col in crime_axes + momentum_axes:
        if col in gdf_master.columns:
            gdf_master[col] = gdf_master[col].fillna(0)

    # --- 7. LOAD COMPILATION MONTHLY HOTSPOT Z-SCORES ---
    print("Loading all monthly Z-Scores...")
    for month in Z_SCORE_MONTHS:
        z_path = os.path.join(config.DASHBOARD_DIR, f"z_scores_2026_{month}.parquet")
        if os.path.exists(z_path):
            df_z = pd.read_parquet(z_path)
            df_z = df_z.rename(columns={'z_score': f'z_score_{month}'})
            gdf_master = gdf_master.merge(df_z[['LSOA_ID', f'z_score_{month}']], on='LSOA_ID', how='left')
            gdf_master[f'z_score_{month}'] = gdf_master[f'z_score_{month}'].fillna(0)
            print(f"  -> Successfully loaded Z-scores for 2026-{month}")
        else:
            print(f"  -> Warning: Asset structural failure. Missing path target: {z_path}")

    # --- 8. GEOSPATIAL POLYGON OPTIMIZATION ---
    if needs_recalc:
        print("Optimizing map layers... Simplifying topology vectors...")
        gdf_master = gpd.GeoDataFrame(gdf_master, geometry='geometry')
        gdf_master['geometry'] = gdf_master.geometry.simplify(0.0008, preserve_topology=True)

        # Isolate minimal boundary features to conserve web transmission bandwidth
        minimal_gdf = gdf_master[['LSOA_ID', 'geometry']].reset_index(drop=True)

        with open(geojson_path, 'w') as f:
            json.dump(minimal_gdf.__geo_interface__, f)
        gdf_master = gdf_master.drop(columns=['geometry'])

    with open(geojson_path, 'r') as f:
        baked_geojson = json.load(f)

    gdf_master = pd.DataFrame(gdf_master).set_index('LSOA_ID', drop=False)
    print("Data Engine Fully Loaded and Ready.")

    return gdf_master, df_forecast, df_time, crime_axes, momentum_axes, baked_geojson