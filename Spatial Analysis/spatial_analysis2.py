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
    # Dynamically placing the output folder in the project root
    output_folder = os.path.join(config.SPATIAL_DIR, "pdf_report_maps")
    os.makedirs(output_folder, exist_ok=True)
    print(f"Output directory '{output_folder}/' is ready.")

    print("Loading geographic shapefile...")

    # Using config for the LSOA boundaries
    map_path = config.LSOA_SHAPEFILE
    gdf_map = gpd.read_file(map_path)
    gdf_map = gdf_map.rename(columns={'LSOA21CD': 'LSOA_ID'})

    print("Calculating the national geographic borders (this takes a minute, but only happens once)...")
    w = libpysal.weights.Queen.from_dataframe(gdf_map)
    w.transform = 'R'

    # Using config for the Prophet forecast results
    df_predictions = pd.read_csv(config.SUMMER_FORECAST_CSV)
    df_predictions['ds'] = pd.to_datetime(df_predictions['ds'])

    global_vmax = df_predictions['yhat'].quantile(0.99)

    months_to_plot = ['2026-04-01', '2026-05-01', '2026-06-01', '2026-07-01', '2026-08-01']

    bboxes = {
        'London': {'xlim': (500000, 560000), 'ylim': (150000, 200000)}
    }

    for target_date in months_to_plot:
        month_str = pd.to_datetime(target_date).strftime('%Y_%m')

        monthly_preds = df_predictions[df_predictions['ds'] == target_date].copy()

        monthly_map_data = gdf_map.merge(monthly_preds, on='LSOA_ID', how='left')
        monthly_map_data['yhat'] = monthly_map_data['yhat'].fillna(0)

        print("Calculating shifting spatial hotspots...")
        gi_star = G_Local(monthly_map_data['yhat'], w, transform='R', star=True)

        monthly_map_data['z_score'] = gi_star.Zs
        monthly_map_data['p_value'] = gi_star.p_sim

        print("Rendering National Map...")
        fig, ax = plt.subplots(1, 1, figsize=(10, 10))
        monthly_map_data.plot(
            column='yhat', cmap='YlOrRd', linewidth=0.05, ax=ax, edgecolor='0.7',
            vmax=global_vmax, legend=True,
            legend_kwds={'label': "Predicted Crime Intensity Index Score", 'orientation': "vertical", 'shrink': 0.6}
        )
        ax.axis('off')
        plt.title(f'National Crime Intensity Forecast ({month_str})', fontsize=16, fontweight='bold')
        plt.savefig(f'{output_folder}/forecast_national_{month_str}.png', dpi=300, bbox_inches='tight')
        plt.close(fig)

        fig, ax = plt.subplots(1, 1, figsize=(8, 8))
        monthly_map_data.plot(
            column='yhat', cmap='YlOrRd', linewidth=0.2, ax=ax, edgecolor='0.3', vmax=global_vmax
        )
        ax.set_xlim(bboxes['London']['xlim'])
        ax.set_ylim(bboxes['London']['ylim'])
        ax.axis('off')
        plt.title(f'London Hotspot Forecast ({month_str})', fontsize=16, fontweight='bold')
        plt.savefig(f'{output_folder}/forecast_london_{month_str}.png', dpi=300, bbox_inches='tight')
        plt.close(fig)

        worst_lsoa = monthly_map_data.loc[monthly_map_data['z_score'].idxmax()]

        epicenter_x = worst_lsoa.geometry.centroid.x
        epicenter_y = worst_lsoa.geometry.centroid.y

        dynamic_xlim = (epicenter_x - 10000, epicenter_x + 10000)
        dynamic_ylim = (epicenter_y - 10000, epicenter_y + 10000)

        fig, ax = plt.subplots(1, 1, figsize=(8, 8))
        monthly_map_data.plot(
            column='yhat', cmap='YlOrRd', linewidth=0.2, ax=ax, edgecolor='0.3', vmax=global_vmax
        )
        ax.set_xlim(dynamic_xlim)
        ax.set_ylim(dynamic_ylim)
        ax.axis('off')

        if 'LSOA21NM' in worst_lsoa:
            hotspot_name = worst_lsoa['LSOA21NM']
        else:
            hotspot_name = worst_lsoa['LSOA_ID']

        plt.title(f'Highest Predicted Crime Intensity Score for {month_str} ({hotspot_name})', fontsize=14, fontweight='bold')
        plt.savefig(f'{output_folder}/forecast_dynamic_hotspot_{month_str}.png', dpi=300, bbox_inches='tight')
        plt.close(fig)