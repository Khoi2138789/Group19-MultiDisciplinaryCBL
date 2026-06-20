import os
import sys
import subprocess
import time
import config

# Import papermill, with a graceful exit if it's missing
try:
    import papermill as pm
except ImportError:
    print("\n CRITICAL ERROR: 'papermill' is not installed.")
    print(" Please install it by running: pip install papermill")
    sys.exit(1)


def run_script(script_path):
    """Executes a python script or Jupyter notebook using the current environment."""
    script_name = os.path.basename(script_path)
    print(f"\n[{time.strftime('%H:%M:%S')}] ==================================================")
    print(f"[{time.strftime('%H:%M:%S')}] STARTING: {script_name}")
    print(f"[{time.strftime('%H:%M:%S')}] ==================================================")

    start_time = time.time()
    success = False

    # Route execution based on file extension
    if script_path.endswith('.ipynb'):
        try:
            # Execute the notebook headlessly.
            # Using the same path for both arguments overwrites the notebook in-place
            # with the new cell outputs.
            pm.execute_notebook(
                input_path=script_path,
                output_path=script_path
            )
            success = True
        except pm.exceptions.PapermillExecutionError as e:
            # Papermill throws an exception if a cell fails, rather than a return code
            print(f"\n[{time.strftime('%H:%M:%S')}] !!! JUPYTER CELL EXECUTION FAILED !!!")
            print(f"Details: {e}")
            success = False
        except Exception as e:
            print(f"\n[{time.strftime('%H:%M:%S')}] !!! UNEXPECTED NOTEBOOK ERROR !!!")
            print(f"Details: {e}")
            success = False

    else:
        # Standard .py execution
        result = subprocess.run([sys.executable, script_path], capture_output=False, text=True)
        if result.returncode == 0:
            success = True
        else:
            print(f"\n[{time.strftime('%H:%M:%S')}] !!! CRITICAL ERROR: exit code {result.returncode} !!!")
            success = False

    elapsed_time = time.time() - start_time

    # Final success/fail logging
    if success:
        print(f"[{time.strftime('%H:%M:%S')}] SUCCESS: {script_name} completed in {elapsed_time:.2f} seconds.")
        return True
    else:
        print(f"[{time.strftime('%H:%M:%S')}] !!! CRITICAL ERROR: {script_name} failed to complete. !!!")
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

        # --- PHASE 4: Spatial Analysis ---
        os.path.join(config.SPATIAL_DIR, "spatial_analysis2.py"),
        os.path.join(config.SPATIAL_DIR, "spatial_analysis_z_scores.py"),

        # --- PHASE 5: Dashboard Asset Baking & Network Construction ---
        os.path.join(config.DASHBOARD_DIR, "convert_data.py"),
        os.path.join(config.DASHBOARD_DIR, "map_construction.py"),
        os.path.join(config.PROPHET_DIR, "linechart.py"),

        # --- PHASE 6: Contextualization analysis ---
        os.path.join(config.CONTEXT_DIR, "crime_IMD_correlation.ipynb")
    ]

    # Sequential execution loop with fail-fast validation
    for step in steps:
        if not os.path.exists(step):
            print(f"\n CRITICAL ERROR: Script missing at {step}")
            print(" Pipeline aborted. Please check your filenames and paths in pipeline.py.")
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