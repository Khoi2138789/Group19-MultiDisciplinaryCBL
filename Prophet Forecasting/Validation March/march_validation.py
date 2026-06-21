import duckdb
import pandas as pd
from sklearn.metrics import mean_absolute_error

import config
import config
import os

con = duckdb.connect(':memory:')

#Storing real crime data of March 2026 into the variable real_data_path.
real_data_path = os.path.join(config.VALIDATION_DIR_MARCH, "**", "*-street.csv").replace('\\', '/')
query_real_data = f"""
    SELECT 
        "LSOA code" AS LSOA_ID,
        SUM(
            CASE 
                WHEN TRIM("Crime type") = 'Violence and sexual offences' THEN 1058.556
                WHEN TRIM("Crime type") = 'Burglary' THEN 564.016
                WHEN TRIM("Crime type") = 'Drugs' THEN 666.678
                WHEN TRIM("Crime type") = 'Possession of weapons' THEN 1710.724
                WHEN TRIM("Crime type") = 'Robbery' THEN 993.551
                ELSE 0 
            END
        ) AS actual_crime_score
    FROM read_csv_auto('{real_data_path}') 
    WHERE 
        "LSOA code" IS NOT NULL
        AND "LSOA code" LIKE 'E%'
    GROUP BY 
        "LSOA code"
"""

df_march = con.execute(query_real_data).df()

#Reading the predictions of March 2026.
df_forecast = pd.read_csv(config.VALIDATION_FORECAST_MARCH_CSV)

#Merging the predictions with the real crime intensity scores.
validation_df = df_forecast.merge(df_march, on='LSOA_ID', how='left')

#Filling rows without real crime scores with the value 0 at the actual_crime_score column.
validation_df['actual_crime_score'] = validation_df['actual_crime_score'].fillna(0)

#Dropping LSOAs where Prophet made no prediction (fair comparison).

clean_validation_df = validation_df[(validation_df['yhat'] > 0) & (validation_df['actual_crime_score'] > 0)]

#Calculating mean absolute error.
mae = mean_absolute_error(clean_validation_df['actual_crime_score'], clean_validation_df['yhat'])

print("Validation Results (March 2026)")
print(f"Total English LSOAs: {len(validation_df)}")
print(f"Valid LSOAs Evaluated: {len(clean_validation_df)}")
print(f"LSOAs Excluded: {len(validation_df) - len(clean_validation_df)}")
print(f"Mean Absolute Error: {mae:.2f} Crime Intensity Score Points")


# Calculate the 20th and 80th percentiles of the actual crime scores
q20 = clean_validation_df['actual_crime_score'].quantile(0.20)
q80 = clean_validation_df['actual_crime_score'].quantile(0.80)

# Split the dataframe into three stratified tiers
low_crime = clean_validation_df[clean_validation_df['actual_crime_score'] <= q20]
high_crime = clean_validation_df[clean_validation_df['actual_crime_score'] >= q80]
mid_crime = clean_validation_df[(clean_validation_df['actual_crime_score'] > q20) & (clean_validation_df['actual_crime_score'] < q80)]

# Calculate MAE for each specific tier
mae_low = mean_absolute_error(low_crime['actual_crime_score'], low_crime['yhat'])
mae_mid = mean_absolute_error(mid_crime['actual_crime_score'], mid_crime['yhat'])
mae_high = mean_absolute_error(high_crime['actual_crime_score'], high_crime['yhat'])

print(f"Bottom 20%")
print(f"  Count: {len(low_crime)} LSOAs")
print(f"  MAE:   {mae_low:.2f} Crime Intensity Points")
print(f"\nMiddle 60%")
print(f"  Count: {len(mid_crime)} LSOAs")
print(f"  MAE:   {mae_mid:.2f} Crime Intensity Points")
print(f"\nTop 20%")
print(f"  Count: {len(high_crime)} LSOAs")
print(f"  MAE:   {mae_high:.2f} Crime Intensity Points")