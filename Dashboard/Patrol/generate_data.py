import geopandas as gpd
import pandas as pd
from libpysal.weights import Queen
import json
import sys
import os
append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import config

lsoa = gpd.read_file(config.LSOA_SHAPEFILE)
pfa = gpd.read_file(config.PFA_SHAPEFILE)

remove = [
    "Greater Manchester",
    "North Wales",
    "Dyfed-Powys",
    "South Wales",
    "Gwent"
]

pfa = pfa[~pfa["PFA21NM"].isin(remove)]

months = ['04', '05', '06', '07', '08']
lsoa = lsoa.rename(columns={'LSOA21CD': 'LSOA_ID'})

for m in months:
    z_path = os.path.join(config.FORECAST_RESULTS_DIR, f"z_scores_2026_{m}.csv")
    z = pd.read_csv(z_path)

    z = z.rename(columns={'z_score': f'z_score_{m}'})

    lsoa = lsoa.merge(z[['LSOA_ID', f'z_score_{m}']], on='LSOA_ID', how='left')

lsoa = lsoa.to_crs(pfa.crs)

joined = gpd.sjoin(
    lsoa,
    pfa,
    how="inner",
    predicate="within"
).reset_index(drop=True)

w = Queen.from_dataframe(joined)

sindex = joined.sindex

adjacency = {}

for idx, neighbours in w.neighbors.items():
    lsoa_id = joined.iloc[idx]["LSOA_ID"]
    adjacency[lsoa_id] = [
        joined.iloc[n]["LSOA_ID"]
        for n in neighbours
    ]

result = {}

print("Building the Patrol Network Graph")
for _, row in joined.iterrows():
    pfa_name = row["PFA21NM"]
    lsoa_code = row["LSOA_ID"]

    all_z = {m: row.get(f"z_score_{m}", 0) for m in months}

    result.setdefault(pfa_name, []).append({
        "lsoa_code": row["LSOA_ID"],
        "lsoa_name": row["LSOA21NM"],
        "lat": row.get("LAT_left", row["geometry"].centroid.y),
        "lon": row.get("LONG_left", row["geometry"].centroid.x),
        "z_score": row.get("z_score_05", 0),
        "all_z_scores": all_z,
        "neighbours": list(set(adjacency.get(lsoa_code, [])) - {lsoa_code})
    })

output_path = os.path.join(config.DASHBOARD_DIR, "lsoa_by_pfa.json")

with open(output_path, "w") as f:
    json.dump(result, f, indent=2)
