import plotly.express as px
import plotly.io as pio
import os
import config

# Import your heavy data directly from your data engine
from data import GDF_MASTER, BAKED_GEOJSON

def compile_base_map():
    print("Stitching 34,000 polygons together... This may take a minute...")

    # We use the raw Python dictionary (BAKED_GEOJSON) here to ensure it doesn't get lost
    fig = px.choropleth_mapbox(
        GDF_MASTER,
        geojson=BAKED_GEOJSON,
        locations='LSOA_ID',
        featureidkey="properties.LSOA_ID",
        color='z_score_04',  # Defaulting to April's Z-scores for the initial load
        custom_data=['LSOA_ID'],
        color_continuous_scale="RdBu_r",
        range_color=[-3, 3],  # Locking the statistical bounds
        mapbox_style="carto-positron",
        zoom=5.5,  # Zoomed out to see the UK natively
        center={"lat": 52.8, "lon": -2.0},
        opacity=0.8
    )

    # MAGIC TRICK: Ultra-thin, semi-transparent borders.
    # This allows you to see the LSOA boundaries without crashing the WebGL rendering engine.
    fig.update_traces(marker_line_width=0, marker_line_color='rgba(255, 255, 255, 0.4)')

    # Lock the UI revision so panning/zooming doesn't reset during callbacks
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, uirevision='constant_map')

    # Save the entire completed visualization using the central config path
    save_path = os.path.join(config.DASHBOARD_DIR, 'precompiled_map.json')
    pio.write_json(fig, save_path)
    print(f"Success! Map securely compiled and saved to: {save_path}")

if __name__ == "__main__":
    compile_base_map()