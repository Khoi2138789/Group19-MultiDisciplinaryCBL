import geopandas as gpd
import pandas as pd
from libpysal.weights import Queen
import json
import matplotlib.pyplot as plt

lsoa = gpd.read_file("/home/user0/Downloads/LSOA_2021_EW_BFC_V10.shp")
pfa = gpd.read_file("/home/user0/Downloads/PFA_DEC_2021_EW_BFC.shp")
z = pd.read_csv("/home/user0/Downloads/z_scores_2026_05.csv")

remove = [
    "Greater Manchester",
    "North Wales",
    "Dyfed-Powys",
    "South Wales",
    "Gwent"
]

pfa = pfa[~pfa["PFA21NM"].isin(remove)]

lsoa = lsoa.merge(
    z,
    left_on="LSOA21CD",
    right_on="LSOA_ID",
    how="left"
)

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

    lsoa = joined.iloc[idx]["LSOA21CD"]

    adjacency[lsoa] = [
        joined.iloc[n]["LSOA21CD"]
        for n in neighbours
    ]

result = {}

for _, row in joined.iterrows():
    pfa = row["PFA21NM"]
    lsoa_code = row["LSOA21CD"]

    result.setdefault(pfa, []).append({
        "lsoa_code": row["LSOA21CD"],
        "lsoa_name": row["LSOA21NM"],
        "lat": row["LAT_left"],
        "long": row["LONG_left"],
        "z_score": row["z_score"],
        "neighbours": list(set(adjacency.get(lsoa_code, [])) - {lsoa_code})
    })

with open("lsoa_by_pfa.json", "w") as f:
    json.dump(result, f, indent=2)