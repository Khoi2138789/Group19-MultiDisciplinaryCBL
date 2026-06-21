import os
import sys
import subprocess
import time
import config
import papermill as pm

def run_script(script_path):
    """Executes a python script or Jupyter notebook using the current environment."""
    script_name = os.path.basename(script_path)
    print(f"\n[{time.strftime('%H:%M:%S')}]")
    print(f"[{time.strftime('%H:%M:%S')}] STARTING: {script_name}")
    success = False

    if script_path.endswith('.ipynb'):
        try:
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
        result = subprocess.run([sys.executable, script_path], capture_output=False, text=True)
        if result.returncode == 0:
            success = True
        else:
            print(f"\n[{time.strftime('%H:%M:%S')}] Error: {result.returncode}")
            success = False

    return success


if __name__ == "__main__":
    pipeline_start = time.time()

    steps = [
        os.path.join(config.DUCKDB_DIR, "DuckDB.py"),
        os.path.join(config.DASHBOARD_DIR, "CCTV data.py"),

        os.path.join(config.PROPHET_DIR, "prophet_january_2026.py"),
        os.path.join(config.VALIDATION_DIR_JANUARY, "january_validation.py"),

        os.path.join(config.PROPHET_DIR, "prophet_february_2026.py"),
        os.path.join(config.VALIDATION_DIR_FEBRUARY, "february_2026_validation.py"),

        os.path.join(config.PROPHET_DIR, "prophet_march_2026.py"),
        os.path.join(config.VALIDATION_DIR_MARCH, "march_validation.py"),

        os.path.join(config.PROPHET_DIR, "prophet_summer_2026.py"),

        os.path.join(config.SPATIAL_DIR, "spatial_analysis2.py"),
        os.path.join(config.SPATIAL_DIR, "spatial_analysis_z_scores.py"),

        os.path.join(config.PATROL_DIR, "generate_data.py"),
        os.path.join(config.PATROL_DIR, "generate_tests.py"),

        os.path.join(config.DASHBOARD_DIR, "convert_data.py"),
        os.path.join(config.DASHBOARD_DIR, "map_construction.py"),
        os.path.join(config.PROPHET_DIR, "linechart.py"),

        os.path.join(config.CONTEXT_DIR, "crime_IMD_correlation.ipynb")
    ]

    for step in steps:
        success = run_script(step)
        if not success:
            print(f"\n PIPELINE DRIFT DETECTED: Execution halted at step: {step}")
            sys.exit(1)

    total_duration = time.time() - pipeline_start
    print(f"\n Total Elapsed Time: {total_duration / 60:.2f} minutes.")
    print(" You can now launch the dashboard via app.py.")