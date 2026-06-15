# Spatial Crime Analytics, Patrol Optimization and Demand Contextualization

This project is designed to analyze and evaluate crime patterns within UK police crime data ranging from January 2023 until March 2026. Together with severity weights, the crime intensity score was computed after which the top five most severe crimes within the UK were chosen to be analyzed. With this project, we visualize localized threat levels, optimize police patrol routing via a random walk and we analyze the drive behind committing crimes via deprivation scores. To ensure reproducible and transparent results, we conducted a structured architecture where heavy data processing and modeling are completely separated.

## Code Pipeline

The running system is split into two parts:

1. **`pipeline.py`:** This file ensures that all necessary datasets are created from external datasets. Additionally, it ensures that the pipeline is automatically run in the correct order to prevent potential confusion regarding running files in the wrong order. `pipeline.py` handles data processing, prophet time series forecasting, spatial z-score calculations and the compilation of geospatial mappings which are used for the dashboard.
2. **`app.py`:** This file is making an interactive dash application by using `data.py`  to prepare the parquet and JSON files. This optimizes the running times of files which make use of geospatial data.

## Repository Structure

```text
.
├── Dashboard/                                   # Web app logic, callbacks and layout
│   ├── Patrol/                                  # Graph code, node navigation and walker logic
│   ├── assets/                                  # Static assets and simplified geometries
│   ├── app.py                                   # Main entry point for the web application
│   ├── callbacks.py                             # Dashboard interactivity and event handling
│   ├── layout.py                                # UI components and structure
│   ├── data.py                                  # Data processor
│   ├── map_construction.py                      # Geographical map creation
│   ├── convert_data.py                          # Parquet conversion
│   ├── CCTV data.py                             # CCTV priority processing logic
│   └── *.parquet / *.json                       # Precompiled spatial and forecast datafiles
├── Datasets/                                    # External datasets containing historical crime records, KMLs, shapefiles and excelsheets --> Download via zipfile
├── DuckDB/                                      # Local database files and processed CSV exports
├── EDA/                                         # Exploratory Data Analysis notebook with results
│   ├── EDA Results/                             # Output plots and statistical findings
│   └── exploration_and_ data_merging.ipynb      # Main data merging and exploration notebook
├── pdf_report_maps/                             # Generated visualizations for exploratory purposes
├── Prophet Forecasting/                         # Predictive time-series modeling and execution
│   ├── Forecasting Results/                     # Csv files containing forecasted results
│   ├── Training Data/                           # Training data for prophet
│   ├── Validation [...]/                        # Model accuracy testing folds (Jan, Feb, March)
│   ├── linechart.py                             # Linechart production of LSOA with high crime intensity score
│   └── prophet_*.py                             # Model execution scripts for specific timeframes
├── Spatial Analysis/                            # Spatial analysis & Hotspot Z-score generation
│   ├── pdf_report_maps/                         # Output maps specific to spatial outputs
│   └── spatial_analysis_*.py                    # Z-score and spatial distribution calculations
├── config.py                                    # Configurations concerning this project
├── pipeline.py                                  # Automated script for dataset generation and preprocessing
└── requirements.txt                             # Python dependencies and package versions.
```

## Setup and Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Khoi2138789/Group19-MultiDisciplinaryCBL.git
   cd Group19-MultiDisciplinaryCBL
   ```

2. **Set up a virtual environment**

   **On macOS and Linux**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

   **On Windows**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download the Datasets**
   
   Download the required datasets via the provided external zip link, extract them and create the  `Datasets` folder where the files can be placed into.



## Running the Code

**1. Run `pipeline.py`**

  Run `pipeline.py` to process the raw datasets, execute the Prophet time-series models and to compute the spatial Z-scores. This process might take hours due to heavy computational work.

**2. Run `app.py` located in the `Dashboard` folder**

  After running `pipeline.py`, it is time to run `app.py` to launch the dashboard which contains our analysis.

**3. View the Tool**

  Navigate to the local server address provided in the terminal and click on it to access our tool.










