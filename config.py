import os

# ==========================================
# 1. ROOT DIRECTORY CONFIGURATION
# ==========================================
# Dit zorgt ervoor dat Python altijd begrijpt waar het project staat,
# ongeacht wie het opent of op welke computer het draait.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# ==========================================
# 2. MAIN DIRECTORIES
# ==========================================
DATA_DIR = os.path.join(PROJECT_ROOT, "Datasets")
DUCKDB_DIR = os.path.join(PROJECT_ROOT, "DuckDB")
PROPHET_DIR = os.path.join(PROJECT_ROOT, "Prophet Forecasting")
DASHBOARD_DIR = os.path.join(PROJECT_ROOT, "Dashboard")
SPATIAL_DIR = os.path.join(PROJECT_ROOT, "Spatial Analysis")

# Sub-directories voor specifieke taken
TRAINING_DATA_DIR = os.path.join(PROPHET_DIR, "Training Data")
FORECAST_RESULTS_DIR = os.path.join(PROPHET_DIR, "Forecasting Results")
VALIDATION_DIR_MARCH = os.path.join(PROPHET_DIR, "Validation March")
VALIDATION_DIR_FEBRUARY = os.path.join(PROPHET_DIR, "Validation February")
VALIDATION_DIR_JANUARY = os.path.join(PROPHET_DIR, "Validation January")
DASHBOARD_ASSETS_DIR = os.path.join(DASHBOARD_DIR, "assets")

# ==========================================
# 3. EXTERNAL RAW DATASETS (Inputs)
# ==========================================
# Deze bestanden MOETEN al in je Datasets map staan voordat je start.

# Ruwe LSOA en PFA boundaries (Shapefiles)
LSOA_SHAPEFILE = os.path.join(
    DATA_DIR,
    "Lower_layer_Super_Output_Areas_December_2021_Boundaries_EW_BFC_V10_-7599572456947714539",
    "LSOA_2021_EW_BFC_V10.shp"
)

PFA_SHAPEFILE = os.path.join(
    DATA_DIR,
    "Police_Force_Areas_Dec_2021_EW_BFC_2022_1799955913995042785",
    "PFA_DEC_2021_EW_BFC.shp"
)

# IMD (Deprivation) scores voor clustering
IMD_DATA_PATH = os.path.join(
    DATA_DIR,
    "File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv"
)

# Crime weights en notifiable offences mapping
CRIME_WEIGHTS_XLS = os.path.join(DATA_DIR, "datatool.xls")
OFFENCE_LIST_ODS = os.path.join(DATA_DIR, "notifiable-offence-and-notifiable-reported-incidents-april-2026.ods")
POLICE_CRIME_DATA = os.path.join(DATA_DIR, "c5e365714b6c98084c564fd69b91ccde80ae9133")


# ==========================================
# 4. INTERMEDIATE FILES (Worden gegenereerd door je code)
# ==========================================
# Deze bestanden hoeven nog niet te bestaan; je scripts maken ze aan.

# Database
DUCKDB_DATABASE = os.path.join(PROJECT_ROOT, "monthly_crime_scores.db")

# CSV's gegenereerd door DuckDB en CCTV data.py
PROPHET_INPUT_CSV = os.path.join(TRAINING_DATA_DIR, "prophet_input.csv")
CRIME_TYPES_CSV = os.path.join(DUCKDB_DIR, "pcp_crime_types.csv")
CCTV_PRIORITY_CSV = os.path.join(DUCKDB_DIR, "cctv_priority.csv")

# Prophet Forecast Outputs
SUMMER_FORECAST_CSV = os.path.join(FORECAST_RESULTS_DIR, "summer_2026_forecast.csv")
VALIDATION_FORECAST_MARCH_CSV = os.path.join(VALIDATION_DIR_MARCH, "march_2026_forecast.csv")
VALIDATION_FORECAST_FEBRUARY_CSV = os.path.join(VALIDATION_DIR_FEBRUARY, "february_2026_forecast.csv")
VALIDATION_FORECAST_JANUARY_CSV = os.path.join(VALIDATION_DIR_JANUARY, "january_2026_forecast.csv")
# ==========================================
# 5. PARQUET FILES (Voor het Dashboard)
# ==========================================
# Jouw bake_to_parquet script converteert de CSV's en slaat ze hier op.

LSOA_BOUNDARIES_PARQUET = os.path.join(DASHBOARD_DIR, "lsoas_boundaries.parquet")
SUMMER_FORECAST_PARQUET = os.path.join(DASHBOARD_DIR, "summer_2026_forecast.parquet")
PROPHET_INPUT_PARQUET = os.path.join(DASHBOARD_DIR, "prophet_input.parquet")
CRIME_TYPES_PARQUET = os.path.join(DASHBOARD_DIR, "pcp_crime_types.parquet")
CCTV_PRIORITY_PARQUET = os.path.join(DASHBOARD_DIR, "cctv_priority.parquet")