import plotly.express as px
import plotly.io as pio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from data import load_and_prepare_data

def compile_base_map():
    print("Stitching 34,000 polygons together... This may take a minute...")

    GDF_MASTER, _, _, _, _, BAKED_GEOJSON = load_and_prepare_data()

    fig = px.choropleth_mapbox(
        GDF_MASTER,
        geojson=BAKED_GEOJSON,
        locations='LSOA_ID',
        featureidkey="properties.LSOA_ID",
        color='z_score_04',
        custom_data=['LSOA_ID'],
        color_continuous_scale="RdBu_r",
        range_color=[-3, 3],
        mapbox_style="carto-positron",
        zoom=5.5,
        center={"lat": 52.8, "lon": -2.0},
        opacity=0.8
    )

    fig.update_traces(marker_line_width=0, marker_line_color='rgba(255, 255, 255, 0.4)')

    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, uirevision='constant_map')

    save_path = os.path.join(config.DASHBOARD_DIR, 'precompiled_map.json')
    pio.write_json(fig, save_path)
    print(f"Success! Map securely compiled and saved to: {save_path}")

if __name__ == "__main__":
    compile_base_map()