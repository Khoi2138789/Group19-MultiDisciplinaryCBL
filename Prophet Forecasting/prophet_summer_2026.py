import pandas as pd
from prophet import Prophet
import concurrent.futures
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import warnings
import logging
import config

# Not allowing prophet to send warning messages in the terminal.
warnings.filterwarnings('ignore')
logging.getLogger('cmdstanpy').setLevel(logging.WARNING)


def forecast_single_lsoa_summer(lsoa_id, historical_data):
    """
    This function takes one LSOA and predicts its future for the next 5 months.
    """
    try:
        # Making sure that the prediction will be 0 when there are less than 2 months containing crime data.
        if len(historical_data) < 2:
            dates = pd.date_range(start='2026-04-01', periods=5, freq='MS')
            return pd.DataFrame({
                'ds': dates,
                'yhat': [0] * 5,
                'yhat_lower': [0] * 5,
                'yhat_upper': [0] * 5,
                'LSOA_ID': [lsoa_id] * 5
            })

        # Making sure Prophet uses the Month column as the time stamps and the Total CII score as the data to train for.
        df = historical_data.rename(columns={'Month': 'ds', 'Total_CII_Score': 'y'})

        local_max = df['y'].quantile(0.95)
        df['y'] = df['y'].clip(upper=local_max)

        m = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
        m.fit(df)

        future = m.make_future_dataframe(periods=5, freq='MS')
        forecast = m.predict(future)

        prediction_rows = forecast.tail(5)[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].copy()
        prediction_rows['LSOA_ID'] = lsoa_id

        return prediction_rows

    except Exception as e:
        # Making sure the algorithm does not crash if the future for a specific LSOA cannot be predicted.
        print(f'A prediction cannot be made for {lsoa_id}: {e}')
        return None


if __name__ == '__main__':

    prophet_training_data = pd.read_csv(config.PROPHET_INPUT_CSV)
    prophet_training_data['Month'] = pd.to_datetime(prophet_training_data['Month'])

    start_date = pd.to_datetime('2023-04-01')
    end_date = pd.to_datetime('2026-03-01')

    prophet_training_data = prophet_training_data[
        (prophet_training_data['Month'] >= start_date) &
        (prophet_training_data['Month'] <= end_date)
        ]

    all_lsoas = prophet_training_data['LSOA_ID'].unique()

    total_cores = os.cpu_count()
    safe_cores = 12

    print(f'Detected {total_cores} CPU cores. Performing the multi-month Prophet algorithm with {safe_cores} workers.')

    pd.DataFrame(columns=['ds', 'yhat', 'yhat_lower', 'yhat_upper', 'LSOA_ID']).to_csv(config.SUMMER_FORECAST_CSV,
                                                                                       index=False)

    all_predictions = []

    with concurrent.futures.ProcessPoolExecutor(max_workers=safe_cores) as executor:

        futures = []
        for lsoa in all_lsoas:
            lsoa_data = prophet_training_data[prophet_training_data['LSOA_ID'] == lsoa].copy()
            futures.append(executor.submit(forecast_single_lsoa_summer, lsoa, lsoa_data))

        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            result = future.result()

            if result is not None:
                all_predictions.append(result)
            if (i + 1) % 1000 == 0:
                chunk_df = pd.concat(all_predictions, ignore_index=True)
                chunk_df['yhat'] = chunk_df['yhat'].clip(lower=0)
                chunk_df['yhat_lower'] = chunk_df['yhat_lower'].clip(lower=0)
                chunk_df['yhat_upper'] = chunk_df['yhat_upper'].clip(lower=0)

                chunk_df.to_csv(config.SUMMER_FORECAST_CSV, mode='a', header=False, index=False)

                print(f'Safely saved {i + 1} / {len(all_lsoas)} LSOAs to disk.')

                all_predictions = []

    if len(all_predictions) > 0:
        chunk_df = pd.concat(all_predictions, ignore_index=True)
        chunk_df['yhat'] = chunk_df['yhat'].clip(lower=0)
        chunk_df['yhat_lower'] = chunk_df['yhat_lower'].clip(lower=0)
        chunk_df['yhat_upper'] = chunk_df['yhat_upper'].clip(lower=0)

        chunk_df.to_csv(config.SUMMER_FORECAST_CSV, mode='a', header=False, index=False)
        print("Final batch saved successfully.")

    saved_df = pd.read_csv(config.SUMMER_FORECAST_CSV)
    print(saved_df.head(10))