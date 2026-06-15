import pandas as pd
import geopandas as gpd
import os
import json
import config

# --- 1. CONFIGURATION & FILE PATHS (UPDATED FOR PARQUET) ---
# We now rely entirely on config.py for dynamic pathing
SHAPEFILE_PATH = config.LSOA_BOUNDARIES_PARQUET
FORECAST_PATH = config.SUMMER_FORECAST_PARQUET
HISTORICAL_TIME_SERIES_PATH = config.PROPHET_INPUT_PARQUET
HISTORICAL_CRIME_TYPES_PATH = config.CRIME_TYPES_PARQUET
CCTV_PRIORITY_PATH = config.CCTV_PRIORITY_PARQUET

# Tell the dashboard which Z-score months to look for
Z_SCORE_MONTHS = ['04', '05', '06', '07', '08']


def load_and_prepare_data():
    print("Initializing Dashboard Data Engine...")

    # Using the config asset directory
    assets_dir = config.DASHBOARD_ASSETS_DIR
    os.makedirs(assets_dir, exist_ok=True)
    geojson_path = os.path.join(assets_dir, 'lsoas.json')
    needs_recalc = not os.path.exists(geojson_path)

    # --- 2. LOAD GEOGRAPHY ---
    if needs_recalc:
        print("First-time setup: Loading GeoParquet boundaries with geometry...")
        gdf_map = gpd.read_parquet(SHAPEFILE_PATH)
    else:
        print("High-res map found! Loading lightweight Parquet boundaries...")
        # pd.read_parquet allows us to only load specific columns, saving even more RAM
        gdf_map = pd.read_parquet(SHAPEFILE_PATH, columns=['LSOA21CD', 'LSOA21NM'])

    gdf_map = gdf_map.rename(columns={'LSOA21CD': 'LSOA_ID', 'LSOA21NM': 'LSOA_NAME'})

    # --- 3. LOAD & PIVOT CRIME TYPES ---
    print("Pivoting Crime Type profiles...")
    df_types = pd.read_parquet(HISTORICAL_CRIME_TYPES_PATH)
    df_pcp_types = df_types.pivot(index='LSOA_ID', columns='Crime_Type', values='Total_Intensity').fillna(
        0).reset_index()
    crime_axes = [col for col in df_pcp_types.columns if col != 'LSOA_ID']

    # --- 4. LOAD & PIVOT HISTORICAL MOMENTUM ---
    print("Pivoting Temporal Momentum profiles...")
    df_time = pd.read_parquet(HISTORICAL_TIME_SERIES_PATH)
    df_time['Month'] = pd.to_datetime(df_time['Month'])
    df_time['Year'] = df_time['Month'].dt.year

    df_time_pcp = df_time[df_time['Year'] <= 2025]
    df_yearly = df_time_pcp.groupby(['LSOA_ID', 'Year'])['Total_CII_Score'].mean().reset_index()
    df_pcp_momentum = df_yearly.pivot(index='LSOA_ID', columns='Year', values='Total_CII_Score').fillna(0).reset_index()

    df_pcp_momentum.columns = [str(col) if isinstance(col, int) else col for col in df_pcp_momentum.columns]
    momentum_axes = [col for col in df_pcp_momentum.columns if col != 'LSOA_ID']

    # --- 5. LOAD PROPHET FORECASTS ---
    print("Loading Summer Predictions...")
    df_forecast = pd.read_parquet(FORECAST_PATH)
    df_forecast['ds'] = pd.to_datetime(df_forecast['ds'])

    # Clip the raw forecast so the time series chart doesn't show negative numbers
    df_forecast['yhat'] = df_forecast['yhat'].clip(lower=0)
    df_forecast['yhat_lower'] = df_forecast['yhat_lower'].clip(lower=0)
    df_forecast['yhat_upper'] = df_forecast['yhat_upper'].clip(lower=0)

    # --- 6. MERGE THE SPATIAL MASTER TABLE ---
    print("Merging Spatial Master Dataset...")
    gdf_master = gdf_map.merge(df_pcp_types, on='LSOA_ID', how='left')
    gdf_master = gdf_master.merge(df_pcp_momentum, on='LSOA_ID', how='left')

    # CCTV
    print("Loading CCTV Priority Rankings...")

    if os.path.exists(CCTV_PRIORITY_PATH):
        df_cctv = pd.read_parquet(CCTV_PRIORITY_PATH)

        df_cctv["LSOA_ID"] = df_cctv["LSOA_ID"].astype(str)

        cctv_cols = [
            "LSOA_ID",
            "unsolved_non_severe",
            "total_non_severe",
            "priority_level",
            "cctv_score",
            "cctv_rank"
        ]

        gdf_master = gdf_master.merge(
            df_cctv[cctv_cols],
            on="LSOA_ID",
            how="left"
        )

        for col in [
            "unsolved_non_severe",
            "total_non_severe",
            "priority_level",
            "cctv_score",
            "cctv_rank"
        ]:
            gdf_master[col] = gdf_master[col].fillna(0)

        print("  -> CCTV priority data loaded.")

    else:
        print("  -> Warning: cctv_priority.parquet not found.")

        gdf_master["unsolved_non_severe"] = 0
        gdf_master["total_non_severe"] = 0
        gdf_master["priority_level"] = 0
        gdf_master["cctv_score"] = 0
        gdf_master["cctv_rank"] = 0

    forecast_agg = df_forecast.groupby('LSOA_ID')[['yhat', 'yhat_lower', 'yhat_upper']].mean().reset_index()

    # CONSTRAINT: Clip to 0 (Physically impossible for crime to be negative)
    forecast_agg['yhat'] = forecast_agg['yhat'].clip(lower=0)
    forecast_agg['yhat_lower'] = forecast_agg['yhat_lower'].clip(lower=0)
    forecast_agg['yhat_upper'] = forecast_agg['yhat_upper'].clip(lower=0)

    forecast_agg['LSOA_ID'] = forecast_agg['LSOA_ID'].astype(str)
    gdf_master = gdf_master.merge(forecast_agg, on='LSOA_ID', how='left')

    for col in ['yhat', 'yhat_lower', 'yhat_upper']:
        if col in gdf_master.columns:
            gdf_master[col] = gdf_master[col].fillna(0)

    for col in crime_axes + momentum_axes:
        if col in gdf_master.columns:
            gdf_master[col] = gdf_master[col].fillna(0)

    # --- 6.5 LOAD ALL SPATIAL HOTSPOT Z-SCORES ---
    print("Loading all monthly Z-Scores...")
    for month in Z_SCORE_MONTHS:
        # Looking in the FORECAST folder and reading the CSV instead of parquet
        z_path = os.path.join(config.DASHBOARD_DIR, f"z_scores_2026_{month}.parquet")

        if os.path.exists(z_path):
            df_z = pd.read_parquet(z_path)

            # Rename 'z_score' to 'z_score_04', 'z_score_05', etc., to avoid overlapping columns
            df_z = df_z.rename(columns={'z_score': f'z_score_{month}'})

            # Merge it onto the master table
            gdf_master = gdf_master.merge(df_z[['LSOA_ID', f'z_score_{month}']], on='LSOA_ID', how='left')

            # Safety catch: Fill missing scores with 0
            gdf_master[f'z_score_{month}'] = gdf_master[f'z_score_{month}'].fillna(0)
            print(f"  -> Successfully loaded Z-scores for 2026-{month}")
        else:
            print(f"  -> Warning: Could not find {z_path}")

    # --- 7. SPATIAL OPTIMIZATION ---
    if needs_recalc:
        gdf_master = gpd.GeoDataFrame(gdf_master, geometry='geometry')

        # print("Simplifying polygons for browser rendering...")
        gdf_master['geometry'] = gdf_master.geometry.simplify(0.0008, preserve_topology=True)

        minimal_gdf = gdf_master[['LSOA_ID', 'geometry']].reset_index(drop=True)

        with open(geojson_path, 'w') as f:
            json.dump(minimal_gdf.__geo_interface__, f)

        gdf_master = gdf_master.drop(columns=['geometry'])

    # Reload the file into memory as a dictionary so Dash can use it
    with open(geojson_path, 'r') as f:
        baked_geojson = json.load(f)

    gdf_master = pd.DataFrame(gdf_master).set_index('LSOA_ID', drop=False)

    print("Data Engine Fully Loaded and Ready.")

    return gdf_master, df_forecast, df_time, crime_axes, momentum_axes, baked_geojson


GDF_MASTER, DF_FORECAST, DF_HISTORICAL, CRIME_AXES, MOMENTUM_AXES, BAKED_GEOJSON = load_and_prepare_data()
