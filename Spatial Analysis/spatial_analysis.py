import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import libpysal
from esda.getisord import G_Local

df_predictions = pd.read_csv(r"C:\Users\20241114\PycharmProjects\PythonProject\Prophet Forecasting\Validation March\march_2026_forecast.csv")

#Making sure that we only will analyze English LSOAs.
df_predictions = df_predictions[df_predictions['LSOA_ID'].str.startswith('E')]
#Making sure that LSOAs with negative value predictions will obtain a prediction of value 0.
df_predictions['yhat'] = df_predictions['yhat'].clip(lower=0)

#Reading the shapefile containing all coordinates of every LSOA in England.
map_path = r"C:\Users\20241114\PycharmProjects\PythonProject\Data\Lower_layer_Super_Output_Areas_December_2021_Boundaries_EW_BFC_V10_-7599572456947714539\LSOA_2021_EW_BFC_V10.shp"
gdf_map = gpd.read_file(map_path)

#Renaming LSOA21CD to LSOA_ID to be able to perform a left join.
gdf_map = gdf_map.rename(columns={'LSOA21CD': 'LSOA_ID'})
map_data = gdf_map.merge(df_predictions, on='LSOA_ID', how='left')
#Providing LSOAs without any prediction the prediction value of 0.
map_data['yhat'] = map_data['yhat'].fillna(0)
vmax_limit = map_data['yhat'].quantile(0.99)

fig, ax = plt.subplots(1, 1, figsize=(12, 12))
map_data.plot(
    column= 'yhat',
    cmap= 'YlOrRd',
    linewidth= 0.05,
    ax= ax,
    edgecolor= '0.7',
    vmax= vmax_limit,
    legend= True,
    legend_kwds= {'label': "Predicted Crime Intensity Index Scores", 'orientation': "vertical"}
)

ax.axis('off')
plt.title('Crime Intensity Score Forecast of England March 2026', fontsize= 16, fontweight= 'bold')
plt.annotate('Source: UK Home Office & Cambridge Crime Harm Index',
             xy= (0.1, 0.05), xycoords= 'figure fraction', fontsize= 8)

plt.savefig(r"C:\Users\20241114\PycharmProjects\PythonProject\Prophet Forecasting\Validation March\forecast_map_march_2026.png", dpi= 400, bbox_inches= 'tight')
plt.show()

#Creating the weight matrix representing neighboring LSOAs via queen contiguity.
w = libpysal.weights.Queen.from_dataframe(map_data)
#Ensuring LSOA and neighbors get smoothened for fair .cluster analysis.
w.transform = 'R'
#Calculating the Getis-Ord Gi* statistic on the predicted crime intensity scores using the LSOA and its neighbors.
gi_star = G_Local(map_data['yhat'], w, transform='R', star=True)

#Adding corresponding z-scores and p-values of each LSOA to the dataframe.
map_data['z_score'] = gi_star.Zs
map_data['p_value'] = gi_star.p_sim

#Filtering out statistically significant clusters of LSOAs for pointing out where the police needs to pay attention to.
significant_hotspots = map_data[(map_data['z_score'] > 1.96) & (map_data['p_value'] < 0.05)].copy()
#Sorting the LSOA clusters by z-score in descending order.
hotspots = significant_hotspots.sort_values(by='z_score', ascending=False)
hotspots = hotspots.rename(columns={
    'LSOA_ID': 'Lsoa_id',
    'LSOA21NM': 'Lsoa_name',
    'yhat': 'Predicted_crime_intensity_score',
    'z_score': 'z_score',
    'p_value': 'p_value'
})

allocations_table = hotspots[['Lsoa_id', 'Lsoa_name', 'Predicted_crime_intensity_score', 'z_score', 'p_value']].head(15)
print(allocations_table)
print(hotspots.count())