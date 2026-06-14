import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import os

# --- 1. Force Academic Typesetting ---
# This ensures the Matplotlib output matches LaTeX document fonts
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 11,
    'axes.labelsize': 12,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.figsize': (8, 4.5)
})

# --- 2. Load historical and forecasted data ---
df_historical = pd.read_csv('Training Data/prophet_input.csv')
df_forecast = pd.read_csv('Forecasting Results/summer_2026_forecast.csv')

# --- 3. Define exact column names ---
lsoa_col = 'LSOA_ID'
date_col_historical = 'Month'
target_col_historical = 'Total_CII_Score'
date_col_forecast = 'ds'

# --- 4. Dynamically select the highest-severity LSOA with stable historical data ---
# Count how many historical months of data each LSOA has
historical_counts = df_historical.groupby(lsoa_col)[date_col_historical].count()

# Filter for LSOAs that have a robust history (e.g., at least 30 months of records)
# This strictly prevents Prophet from exploding due to sparse data
valid_lsoas = historical_counts[historical_counts >= 30].index

# Filter the forecast dataframe to only include these stable LSOAs
stable_forecasts = df_forecast[df_forecast[lsoa_col].isin(valid_lsoas)]

# Dynamically grab the LSOA with the highest forecasted crime intensity
target_lsoa = stable_forecasts.groupby(lsoa_col)['yhat'].sum().idxmax()

# --- 5. Isolate the data ---
hist_lsoa = df_historical[df_historical[lsoa_col] == target_lsoa].copy()
fore_lsoa = df_forecast[df_forecast[lsoa_col] == target_lsoa].copy()

# Ensure date columns are formatted as datetime objects
hist_lsoa[date_col_historical] = pd.to_datetime(hist_lsoa[date_col_historical])
fore_lsoa[date_col_forecast] = pd.to_datetime(fore_lsoa[date_col_forecast])

# --- 6. Initialize and Build the Plot ---
fig, ax = plt.subplots()

# Plot historical actuals with a continuous line and dot markers
ax.plot(hist_lsoa[date_col_historical], hist_lsoa[target_col_historical],
         color='black', marker='.', linestyle='-', linewidth=1,
         label='Observed Crime Intensity')

# Plot the Prophet forecast
ax.plot(fore_lsoa[date_col_forecast], fore_lsoa['yhat'], color='#0072B2', linewidth=1.5, label='Forecasted Trend')

# Plot the uncertainty intervals
ax.fill_between(fore_lsoa[date_col_forecast], fore_lsoa['yhat_lower'], fore_lsoa['yhat_upper'],
                 color='#0072B2', alpha=0.2, label='Uncertainty Interval')

# --- 7. Academic Formatting & Cleanup ---
ax.set_xlabel('Date')
ax.set_ylabel('Crime Intensity Score')

# Mark the start of the final summer forecast
ax.axvline(pd.to_datetime('2026-03-31'), color='red', linestyle='--', linewidth=1, label='Forecast Start')

# Remove legend border for a cleaner look
ax.legend(loc='upper left', frameon=False)

# Make the grid subtle
ax.grid(True, linestyle='--', alpha=0.4)

# Add comma separators to the Y-axis (e.g., 200000 -> 200,000)
ax.yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))

# --- 8. Save at high resolution ---
plt.tight_layout()

save_dir = 'Prophet Forecasting/Report/pdf_report_chart'
file_name = 'forecast_temporal_highest_lsoa.png'

# Ensure the directory exists safely
os.makedirs(save_dir, exist_ok=True)
full_path = os.path.join(save_dir, file_name)

# facecolor='white' prevents transparent/dark background artifacts
plt.savefig(full_path, dpi=600, bbox_inches='tight', facecolor='white')
print(f"The dynamically selected LSOA is: {target_lsoa}")