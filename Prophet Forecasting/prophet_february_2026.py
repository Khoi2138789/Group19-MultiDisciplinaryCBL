import pandas as pd
from prophet import Prophet
import concurrent.futures
import os
import warnings
import logging

#Not allowing prophet to send warning messages in the terminal.
warnings.filterwarnings('ignore')
logging.getLogger('cmdstanpy').setLevel(logging.WARNING)


def forecast_single_lsoa(lsoa_id, historical_data):
    """
    This function takes one LSOA and predicts its future.
    """
    try:
        #Making sure that the prediction will be 0 when there are less than 2 months containing crime data.
        if len(historical_data) < 2:
            return pd.DataFrame({
                'ds': [pd.to_datetime('2026-02-01')], # Updated to February 2026
                'yhat': [0],
                'yhat_lower': [0],
                'yhat_upper': [0],
                'LSOA_ID': [lsoa_id]
            })
        #Making sure Prophet uses the Month column as the time stamps and the Total CII score as the data to train for.
        df = historical_data.rename(columns={'Month': 'ds', 'Total_CII_Score': 'y'})

        local_max = df['y'].quantile(0.95)
        df['y'] = df['y'].clip(upper=local_max)
        #Initializing the model and making sure that the model only accounts for yearly seasonality.
        m = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
        m.fit(df)

        #Predicting only for the next month.
        future = m.make_future_dataframe(periods=1, freq='MS')
        forecast = m.predict(future)

        #Extracting the prediction and attaching the LSOA name to it.
        prediction_row = forecast.tail(1)[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].copy()
        prediction_row['LSOA_ID'] = lsoa_id

        return prediction_row

    except Exception as e:
        #Making sure the algorithm does not crash if the next month for a specific LSOA cannot be predicted.
        print(f'A prediction cannot be made for {lsoa_id}: {e}')
        return None

if __name__ == '__main__':

    #Reading the created csv containing the Crime Intensity Scores for each LSOA for each month.
    prophet_training_data = pd.read_csv(r"C:\Users\20241114\PycharmProjects\PythonProject\Prophet Forecasting\Training Data\prophet_input.csv")
    #Ensuring that the date column does not contain any formatting errors.
    prophet_training_data['Month'] = pd.to_datetime(prophet_training_data['Month'])

    # Updated rolling window: February 2023 to January 2026
    start_date_val = pd.to_datetime('2023-02-01')
    end_date_val = pd.to_datetime('2026-01-01')

    prophet_training_data = prophet_training_data[
        (prophet_training_data['Month'] >= start_date_val) &
        (prophet_training_data['Month'] <= end_date_val)
        ]

    #Extracting all the LSOAs.
    all_lsoas = prophet_training_data['LSOA_ID'].unique()
    #Allowing for only a maximum of n-1 workers for the process.
    total_cores = os.cpu_count()
    safe_cores = 12

    print(f'Detected {total_cores} CPU cores. Performing the Prophet algorithm with {safe_cores} workers.')

    all_predictions = []
    first_batch = True
    output_path = r"C:\Users\20241114\PycharmProjects\PythonProject\Prophet Forecasting\Validation February\february_2026_forecast.csv"

    # Allowing for multiple workers at the same time.
    with concurrent.futures.ProcessPoolExecutor(max_workers=safe_cores) as executor:

        futures = []
        for lsoa in all_lsoas:
            # Assigning for every worker only data of one LSOA at a time.
            lsoa_data = prophet_training_data[prophet_training_data['LSOA_ID'] == lsoa].copy()
            futures.append(executor.submit(forecast_single_lsoa, lsoa, lsoa_data))

        # Storing the forecasting results for each LSOA
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            result = future.result()

            if result is not None:
                all_predictions.append(result)

            # --- BATCH PROCESSING LOGIC ---
            # Every 1,000 LSOAs, process the batch, clip negatives, append to CSV, and clear RAM
            if (i + 1) % 1000 == 0:
                df_batch = pd.concat(all_predictions, ignore_index=True)

                # Clip impossible negative forecasts to 0
                df_batch['yhat'] = df_batch['yhat'].clip(lower=0)
                df_batch['yhat_lower'] = df_batch['yhat_lower'].clip(lower=0)
                df_batch['yhat_upper'] = df_batch['yhat_upper'].clip(lower=0)

                if first_batch:
                    # First batch creates the file and writes the header
                    df_batch.to_csv(output_path, index=False, mode='w')
                    first_batch = False
                else:
                    # Subsequent batches append to the file without writing the header again
                    df_batch.to_csv(output_path, index=False, mode='a', header=False)

                print(f'Appended batch to disk: {i + 1} / {len(all_lsoas)} LSOAs. RAM refreshed.')

                # Clear the list to free up system memory
                all_predictions = []

    # --- FINAL BATCH PROCESSING ---
    # Catch any remaining LSOAs that didn't perfectly fit into a 1,000-item batch at the end
    if all_predictions:
        df_final_batch = pd.concat(all_predictions, ignore_index=True)

        df_final_batch['yhat'] = df_final_batch['yhat'].clip(lower=0)
        df_final_batch['yhat_lower'] = df_final_batch['yhat_lower'].clip(lower=0)
        df_final_batch['yhat_upper'] = df_final_batch['yhat_upper'].clip(lower=0)

        if first_batch:
            df_final_batch.to_csv(output_path, index=False, mode='w')
        else:
            df_final_batch.to_csv(output_path, index=False, mode='a', header=False)

        print(f'Final batch appended. Total LSOAs processed: {len(all_lsoas)}.')