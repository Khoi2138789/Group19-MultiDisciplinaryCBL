import os
import sys
import subprocess
import time
import config


def run_script(script_path):
    """Executes a python script using the current environment interpreter."""
    script_name = os.path.basename(script_path)
    print(f"\n[{time.strftime('%H:%M:%S')}] ==================================================")
    print(f"[{time.strftime('%H:%M:%S')}] STARTING: {script_name}")
    print(f"[{time.strftime('%H:%M:%S')}] ==================================================")

    start_time = time.time()

    # Use sys.executable to guarantee it runs inside your current PyCharm virtual environment
    result = subprocess.run([sys.executable, script_path], capture_output=False, text=True)

    elapsed_time = time.time() - start_time

    if result.returncode == 0:
        print(f"[{time.strftime('%H:%M:%S')}] SUCCESS: {script_name} completed in {elapsed_time:.2f} seconds.")
        return True
    else:
        print(
            f"\n[{time.strftime('%H:%M:%S')}] !!! CRITICAL ERROR: {script_name} failed with exit code {result.returncode} !!!")
        return False


if __name__ == "__main__":
    pipeline_start = time.time()

    print("==================================================")
    print(" INITIALIZING MASTER DATA SCIENCE PIPELINE")
    print(" WARNING: Full end-to-end execution selected.")
    print(" This process includes heavy multi-core forecasting.")
    print(f" Project Root: {config.PROJECT_ROOT}")
    print("==================================================")

    # These paths are mapped precisely to your PyCharm folder structure and config file
    steps = [
        # --- PHASE 1: Data Ingestion & Engineering ---
        os.path.join(config.DUCKDB_DIR, "DuckDB.py"),
        os.path.join(config.DASHBOARD_DIR, "CCTV data.py"),

        # --- PHASE 2: Validation Modeling (January, February, March) ---
        os.path.join(config.PROPHET_DIR, "prophet_january_2026.py"),
        os.path.join(config.VALIDATION_DIR_JANUARY, "january_validation.py"),

        os.path.join(config.PROPHET_DIR, "prophet_february_2026.py"),
        os.path.join(config.VALIDATION_DIR_FEBRUARY, "february_2026_validation.py"),

        os.path.join(config.PROPHET_DIR, "prophet_march_2026.py"),
        os.path.join(config.VALIDATION_DIR_MARCH, "march_validation.py"),

        # --- PHASE 3: Production Forecasting ---
        os.path.join(config.PROPHET_DIR, "prophet_summer_2026.py"),

        # --- PHASE 4: Spatial Analysis (Using your new config variable!) ---
        os.path.join(config.SPATIAL_DIR, "spatial_analysis2.py"),
        os.path.join(config.SPATIAL_DIR, "spatial_analysis_z_scores.py"),

        # --- PHASE 5: Dashboard Asset Baking & Network Construction ---
        os.path.join(config.DASHBOARD_DIR, "convert_data.py"),
        os.path.join(config.DASHBOARD_DIR, "map_construction.py"),
        os.path.join(config.PROPHET_DIR, "linechart.py")
    ]

    # Sequential execution loop with fail-fast validation
    for step in steps:
        if not os.path.exists(step):
            print(f"\n CRITICAL ERROR: Script missing at {step}")
            print(" Pipeline aborted. Please check your filenames and paths in main_pipeline.py.")
            sys.exit(1)

        success = run_script(step)
        if not success:
            print(f"\n PIPELINE DRIFT DETECTED: Execution halted at step: {step}")
            sys.exit(1)

    total_duration = time.time() - pipeline_start
    print(f"\n==================================================")
    print(f" PIPELINE COMPLETE: All modules executed successfully!")
    print(f" Total Elapsed Time: {total_duration / 60:.2f} minutes.")
    print(f" All reproducible assets have been generated.")
    print(f" You can now safely launch your dashboard via app.py.")
    print(f"==================================================")