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
                'ds': [pd.to_datetime('2026-03-01')],
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

    start_date_val = pd.to_datetime('2023-03-01')
    end_date_val = pd.to_datetime('2026-02-01')

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

    #Allowing for multiple workers at the same time.
    with concurrent.futures.ProcessPoolExecutor(max_workers=safe_cores) as executor:

        futures = []
        for lsoa in all_lsoas:
            #Assigning for every worker only data of one LSOA at a time.
            lsoa_data = prophet_training_data[prophet_training_data['LSOA_ID'] == lsoa].copy()
            futures.append(executor.submit(forecast_single_lsoa, lsoa, lsoa_data))

        #Storing the forecasting results for each LSOA for the next month.
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            result = future.result()

            if result is not None:
                all_predictions.append(result)

            if (i + 1) % 1000 == 0:
                print(f'Completed the process for {i + 1} / {len(all_lsoas)} LSOAs.')

    #Creating a dataframe containing all the separate LSOA predictions for the next month.
    df_predictions = pd.concat(all_predictions, ignore_index=True)

    df_predictions['yhat'] = df_predictions['yhat'].clip(lower=0)
    df_predictions['yhat_lower'] = df_predictions['yhat_lower'].clip(lower=0)
    df_predictions['yhat_upper'] = df_predictions['yhat_upper'].clip(lower=0)

    df_predictions.to_csv(r"C:\Users\20241114\PycharmProjects\PythonProject\Prophet Forecasting\Validation March\march_2026_forecast.csv", index=False)

    print(df_predictions.head())