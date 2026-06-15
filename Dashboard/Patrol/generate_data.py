import geopandas as gpd
import pandas as pd
from libpysal.weights import Queen
import json
import os
import config

lsoa = gpd.read_file(config.LSOA_SHAPEFILE)
pfa = gpd.read_file(config.PFA_SHAPEFILE)

# Grabbing the May Z-scores to weight the patrol probabilities
z_path = os.path.join(config.FORECAST_RESULTS_DIR, "z_scores_2026_05.csv")
z = pd.read_csv(z_path)

print("Calculating Queen contiguity (spatial neighbors)...")
w = Queen.from_dataframe(lsoa)

lsoa = lsoa.merge(
    z,
    left_on="LSOA21CD",
    right_on="LSOA_ID",
    how="left"
)

lsoa = lsoa.to_crs(pfa.crs)

print("Mapping LSOAs to Police Force Areas...")
joined = gpd.sjoin(
    lsoa,
    pfa,
    how="left",
    predicate="intersects"
)

sindex = joined.sindex

adjacency = {}

for idx, neighbours in w.neighbors.items():
    lsoa_id = joined.iloc[idx]["LSOA21CD"]
    adjacency[lsoa_id] = [
        joined.iloc[n]["LSOA21CD"]
        for n in neighbours
    ]

result = {}

print("Building Patrol Network Graph...")
for _, row in joined.iterrows():
    pfa_name = row["PFA21NM"]
    lsoa_code = row["LSOA21CD"]

    # Safety catch: use the exact geometry centroid if LAT_left is missing
    lat = row.get("LAT_left", row["geometry"].centroid.y)
    lon = row.get("LONG_left", row["geometry"].centroid.x)

    result.setdefault(pfa_name, []).append({
        "lsoa_code": row["LSOA21CD"],
        "lsoa_name": row["LSOA21NM"],
        "lat": lat,
        "long": lon,
        "z_score": row["z_score"],
        "neighbours": list(set(adjacency.get(lsoa_code, [])) - {lsoa_code})
    })

# Save directly into the Dashboard assets folder so layout.py can import it
output_path = os.path.join(config.DASHBOARD_ASSETS_DIR, "lsoa_by_pfa.json")

with open(output_path, "w") as f:
    json.dump(result, f, indent=2)

print(f"Network graph successfully baked and saved to {output_path}")