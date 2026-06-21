import os
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import libpysal
from esda.getisord import G_Local
import warnings
import config

warnings.filterwarnings('ignore')

if __name__ == '__main__':

    output_folder = os.path.join(config.SPATIAL_DIR, "pdf_report_maps_zscores")
    os.makedirs(output_folder, exist_ok=True)

    map_path = config.LSOA_SHAPEFILE
    gdf_map = gpd.read_file(map_path)
    gdf_map = gdf_map.rename(columns={'LSOA21CD': 'LSOA_ID'})

    gdf_map = gdf_map[gdf_map['LSOA_ID'].str.startswith('E')]

    w = libpysal.weights.Queen.from_dataframe(gdf_map)
    w.transform = 'R'

    df_predictions = pd.read_csv(config.SUMMER_FORECAST_CSV)
    df_predictions['ds'] = pd.to_datetime(df_predictions['ds'])

    months_to_plot = ['2026-04-01', '2026-05-01', '2026-06-01', '2026-07-01', '2026-08-01']

    bboxes = {
        'London': {'xlim': (500000, 560000), 'ylim': (150000, 200000)}
    }

    for target_date in months_to_plot:
        target_dt = pd.to_datetime(target_date)
        month_str = target_dt.strftime('%Y_%m')
        title_month = target_dt.strftime('%B %Y')

        monthly_preds = df_predictions[df_predictions['ds'] == target_date].copy()

        monthly_map_data = gdf_map.merge(monthly_preds, on='LSOA_ID', how='left')
        monthly_map_data['yhat'] = monthly_map_data['yhat'].fillna(0)

        gi_star = G_Local(monthly_map_data['yhat'], w, transform='R', star=True)

        monthly_map_data['z_score'] = gi_star.Zs
        monthly_map_data['p_value'] = gi_star.p_sim

        csv_filename = f"z_scores_{month_str}.csv"
        csv_output_path = os.path.join(config.FORECAST_RESULTS_DIR, csv_filename)
        monthly_map_data[['LSOA_ID', 'z_score']].to_csv(csv_output_path, index=False)

        fig, ax = plt.subplots(1, 1, figsize=(10, 10))
        monthly_map_data.plot(
            column='z_score', cmap='coolwarm', vmin=-3, vmax=3,
            linewidth=0.05, ax=ax, edgecolor='0.7', legend=True,
            legend_kwds={'label': "Getis-Ord Gi* Z-Score (Spatial Significance)", 'orientation': "vertical",
                         'shrink': 0.6}
        )
        ax.axis('off')
        plt.title(f'Spatial Distribution of Crime Intensity Z-Scores Across England for {title_month}', fontsize=16, fontweight='bold')
        plt.savefig(f'{output_folder}/forecast_national_{month_str}.png', dpi=600, bbox_inches='tight')
        plt.close(fig)

        fig, ax = plt.subplots(1, 1, figsize=(8, 8))
        monthly_map_data.plot(
            column='z_score', cmap='coolwarm', vmin=-3, vmax=3,
            linewidth=0.2, ax=ax, edgecolor='0.3'
        )
        ax.set_xlim(bboxes['London']['xlim'])
        ax.set_ylim(bboxes['London']['ylim'])
        ax.axis('off')
        plt.title(f'Spatial Distribution of Crime Intensity Z-Scores Within London for {title_month}', fontsize=16, fontweight='bold')
        plt.savefig(f'{output_folder}/forecast_london_{month_str}.png', dpi=600, bbox_inches='tight')
        plt.close(fig)

        worst_lsoa = monthly_map_data.loc[monthly_map_data['z_score'].idxmax()]
        peak_z = worst_lsoa['z_score']

        epicenter_x = worst_lsoa.geometry.centroid.x
        epicenter_y = worst_lsoa.geometry.centroid.y

        dynamic_xlim = (epicenter_x - 10000, epicenter_x + 10000)
        dynamic_ylim = (epicenter_y - 10000, epicenter_y + 10000)

        fig, ax = plt.subplots(1, 1, figsize=(8, 8))

        monthly_map_data.plot(
            column='z_score', cmap='coolwarm', vmin=-3, vmax=3,
            linewidth=0.2, ax=ax, edgecolor='0.3'
        )
        ax.set_xlim(dynamic_xlim)
        ax.set_ylim(dynamic_ylim)
        ax.axis('off')

        if 'LSOA21NM' in worst_lsoa:
            hotspot_name = worst_lsoa['LSOA21NM']
        else:
            hotspot_name = worst_lsoa['LSOA_ID']

        plt.title(f'Highest Predicted Hotspot for {title_month}\n({hotspot_name} With a Score of {peak_z:.2f})',
                  fontsize=14, fontweight='bold')
        plt.savefig(f'{output_folder}/forecast_dynamic_hotspot_{month_str}.png', dpi=600, bbox_inches='tight')
        plt.close(fig)