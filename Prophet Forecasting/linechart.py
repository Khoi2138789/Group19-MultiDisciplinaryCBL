import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 11,
    'axes.labelsize': 12,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.figsize': (8, 4.5)
})

df_historical = pd.read_csv(config.PROPHET_INPUT_CSV)
df_forecast = pd.read_csv(config.SUMMER_FORECAST_CSV)

lsoa_col = 'LSOA_ID'
date_col_historical = 'Month'
target_col_historical = 'Total_CII_Score'
date_col_forecast = 'ds'

historical_counts = df_historical.groupby(lsoa_col)[date_col_historical].count()

valid_lsoas = historical_counts[historical_counts >= 30].index

stable_forecasts = df_forecast[df_forecast[lsoa_col].isin(valid_lsoas)]

target_lsoa = stable_forecasts.groupby(lsoa_col)['yhat'].sum().idxmax()

hist_lsoa = df_historical[df_historical[lsoa_col] == target_lsoa].copy()
fore_lsoa = df_forecast[df_forecast[lsoa_col] == target_lsoa].copy()

hist_lsoa[date_col_historical] = pd.to_datetime(hist_lsoa[date_col_historical])
fore_lsoa[date_col_forecast] = pd.to_datetime(fore_lsoa[date_col_forecast])
fig, ax = plt.subplots()

ax.plot(hist_lsoa[date_col_historical], hist_lsoa[target_col_historical],
         color='black', marker='.', linestyle='-', linewidth=1,
         label='Observed Crime Intensity')

ax.plot(fore_lsoa[date_col_forecast], fore_lsoa['yhat'], color='#0072B2', linewidth=1.5, label='Forecasted Trend')
ax.fill_between(fore_lsoa[date_col_forecast], fore_lsoa['yhat_lower'], fore_lsoa['yhat_upper'],
                 color='#0072B2', alpha=0.2, label='Uncertainty Interval')

ax.set_xlabel('Date')
ax.set_ylabel('Crime Intensity Score')
ax.axvline(pd.to_datetime('2026-03-31'), color='red', linestyle='--', linewidth=1, label='Forecast Start')
ax.legend(loc='upper left', frameon=False)

ax.grid(True, linestyle='--', alpha=0.4)

ax.yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))

plt.tight_layout()

save_dir = os.path.join(config.PROJECT_ROOT, 'Prophet Forecasting', 'Report', 'pdf_report_chart')
file_name = 'forecast_temporal_highest_lsoa.png'

os.makedirs(save_dir, exist_ok=True)
full_path = os.path.join(save_dir, file_name)

plt.savefig(full_path, dpi=600, bbox_inches='tight', facecolor='white')
print(f"The dynamically selected LSOA is: {target_lsoa}")
print(f"Chart successfully saved to: {full_path}")