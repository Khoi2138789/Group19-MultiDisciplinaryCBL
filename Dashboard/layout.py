import os
import json
import plotly.io as pio
from dash import dcc, html, dash_table
import dash_leaflet as dl
import config

MAP_FILE = os.path.join(config.DASHBOARD_DIR, "precompiled_map.json")

print("Loading pre-compiled map into layout...")
INITIAL_MAP = pio.read_json(MAP_FILE)
INITIAL_MAP.update_traces(hoverinfo="none", hovertemplate=None)
INITIAL_MAP.update_layout(dragmode="lasso")

# Dynamic config-driven pathing for network structures
# New code looking directly in the Dashboard folder
PATROL_NETWORK_PATH = os.path.join(config.DASHBOARD_DIR, "lsoa_by_pfa.json")

print("Loading patrol network mapping layer...")
with open(PATROL_NETWORK_PATH) as f:
    PFA_DATA = json.load(f)


def card_style(extra=None):
    base = {
        "backgroundColor": "white",
        "borderRadius": "16px",
        "boxShadow": "0 8px 24px rgba(15, 23, 42, 0.08)",
        "border": "1px solid #dbe3ef",
        "padding": "18px",
        "width": "100%",
        "boxSizing": "border-box"
    }
    if extra:
        base.update(extra)
    return base


def graph_wrapper_style(height):
    return {
        "height": height,
        "width": "100%",
        "position": "relative"
    }


def graph_style():
    return {
        "position": "absolute",
        "top": 0,
        "left": 0,
        "width": "100%",
        "height": "100%"
    }


def section_title(text):
    return html.H4(
        text,
        style={
            "margin": "0 0 14px 0",
            "color": "#172033",
            "fontSize": "18px",
            "fontWeight": "750"
        }
    )


def make_layout():
    return html.Div(
        style={
            "minHeight": "100vh",
            "width": "100vw",
            "display": "flex",
            "flexDirection": "column",
            "fontFamily": "Arial, sans-serif",
            "backgroundColor": "#f4f7fb",
            "overflowX": "hidden"
        },
        children=[
            dcc.Location(id="url", refresh=True),
            dcc.Store(id="selected-lsoas", data=[]),
            dcc.Store(id="selected-time-window", data=None),

            # HEADER
            html.Div(
                style={
                    "height": "68px",
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center",
                    "padding": "0 24px",
                    "backgroundColor": "#1e2b3c",
                    "color": "white",
                    "boxShadow": "0 2px 8px rgba(0,0,0,0.12)",
                    "zIndex": 100,
                    "flexShrink": 0
                },
                children=[
                    html.H2(
                        "Predictive Crime Intensity & Transparency Explorer",
                        style={
                            "margin": 0,
                            "fontSize": "24px",
                            "fontWeight": "600",
                            "letterSpacing": "-0.02em"
                        }
                    ),
                    html.Button(
                        "⟳ Reset Filters",
                        id="reset-btn",
                        n_clicks=0,
                        style={
                            "cursor": "pointer",
                            "padding": "10px 18px",
                            "backgroundColor": "#245c97",
                            "color": "white",
                            "border": "none",
                            "borderRadius": "12px",
                            "fontWeight": "700"
                        }
                    )
                ]
            ),

            # MAIN CONTAINER
            html.Div(
                id="main-workspace",
                style={
                    "display": "flex",
                    "flexDirection": "column",
                    "gap": "22px",
                    "padding": "22px",
                    "width": "100%",
                    "boxSizing": "border-box"
                },
                children=[
                    # MAP CARD
                    html.Div(
                        style=card_style(),
                        children=[
                            html.Div(
                                style={
                                    "display": "flex",
                                    "justifyContent": "space-between",
                                    "alignItems": "flex-start",
                                    "gap": "20px",
                                    "marginBottom": "14px",
                                    "flexWrap": "wrap"
                                },
                                children=[
                                    html.Div(
                                        children=[
                                            html.H3(
                                                "Spatial Monthly Z-Score & Uncertainty Forecasts",
                                                style={"margin": "0 0 10px 0", "color": "#172033", "fontSize": "20px", "fontWeight": "800"}
                                            ),
                                            dcc.RadioItems(
                                                id="map-view-toggle",
                                                options=[
                                                    {"label": " Severity (Z-Score)", "value": "severity"},
                                                    {"label": " Uncertainty", "value": "uncertainty"}
                                                ],
                                                value="severity",
                                                inline=True,
                                                style={"fontSize": "14px", "color": "#172033"},
                                                inputStyle={"marginRight": "6px", "marginLeft": "0px"},
                                                labelStyle={"marginRight": "18px"}
                                            )
                                        ]
                                    ),
                                    html.Div(
                                        style={"minWidth": "260px"},
                                        children=[
                                            html.Strong("Target Month:", style={"fontSize": "14px", "display": "block", "marginBottom": "6px", "color": "#172033"}),
                                            dcc.Dropdown(
                                                id="month-slider",
                                                options=[
                                                    {"label": "April 2026", "value": 4},
                                                    {"label": "May 2026", "value": 5},
                                                    {"label": "June 2026", "value": 6},
                                                    {"label": "July 2026", "value": 7},
                                                    {"label": "August 2026", "value": 8}
                                                ],
                                                value=4,
                                                clearable=False,
                                                searchable=False,
                                                style={"fontSize": "14px", "color": "#172033"}
                                            )
                                        ]
                                    )
                                ]
                            ),
                            html.Div(
                                style=graph_wrapper_style("760px"),
                                children=[
                                    dcc.Graph(
                                        id="interactive-map",
                                        figure=INITIAL_MAP,
                                        responsive=True,
                                        style=graph_style(),
                                        config={"displayModeBar": True, "scrollZoom": True}
                                    )
                                ]
                            )
                        ]
                    ),

                    # PCP CARD
                    html.Div(
                        style=card_style(),
                        children=[
                            html.Div(
                                style={
                                    "display": "flex",
                                    "justifyContent": "space-between",
                                    "alignItems": "center",
                                    "gap": "18px",
                                    "marginBottom": "14px",
                                    "flexWrap": "wrap"
                                },
                                children=[
                                    html.H3("Yearly Historical Averages & Crime Type Totals", style={"margin": 0, "color": "#172033", "fontSize": "20px", "fontWeight": "800"}),
                                    dcc.RadioItems(
                                        id="pcp-mode-toggle",
                                        options=[
                                            {"label": " Historical Momentum ", "value": "momentum"},
                                            {"label": " Crime Type Profile ", "value": "type"}
                                        ],
                                        value="momentum",
                                        inline=True,
                                        style={"fontSize": "14px", "color": "#172033"},
                                        inputStyle={"marginRight": "6px"},
                                        labelStyle={"marginRight": "18px"}
                                    )
                                ]
                            ),
                            html.Div(
                                style=graph_wrapper_style("460px"),
                                children=[
                                    dcc.Graph(id="pcp-graph", responsive=True, style=graph_style(), config={"displayModeBar": False})
                                ]
                            )
                        ]
                    ),

                    # BOXPLOT CARD
                    html.Div(
                        style=card_style(),
                        children=[
                            section_title("Monthly Predicted Crime Intensity Distribution"),
                            html.Div(
                                style=graph_wrapper_style("430px"),
                                children=[
                                    dcc.Graph(id="distribution-boxplot", responsive=True, style=graph_style(), config={"displayModeBar": False})
                                ]
                            )
                        ]
                    ),

                    # LINE CHART CARD
                    html.Div(
                        style=card_style(),
                        children=[
                            section_title("Historical Monthly Averages & Summer Prediction Trends"),
                            html.Div(
                                style=graph_wrapper_style("430px"),
                                children=[
                                    dcc.Graph(id="timeseries-graph", responsive=True, style=graph_style(), config={"displayModeBar": False})
                                ]
                            )
                        ]
                    ),

                    # GRANULAR TABLE CARD
                    html.Div(
                        style=card_style(),
                        children=[
                            section_title("Granular LSOA Forecasts & Selected Temporal Averages"),
                            dash_table.DataTable(
                                id="details-datatable",
                                page_size=10,
                                sort_action="native",
                                filter_action="native",
                                sort_mode="multi",
                                style_table={"overflowX": "auto", "borderRadius": "12px", "overflow": "hidden"},
                                style_header={"backgroundColor": "#eef4fb", "fontWeight": "bold", "border": "1px solid #dbe3ef", "color": "#172033", "fontSize": "14px"},
                                style_cell={"textAlign": "left", "padding": "11px", "fontFamily": "Arial, sans-serif", "fontSize": "13px", "border": "1px solid #edf1f7", "color": "#263244", "minWidth": "120px", "maxWidth": "360px", "whiteSpace": "normal"},
                                style_data_conditional=[{"if": {"row_index": "odd"}, "backgroundColor": "#fafcff"}]
                            )
                        ]
                    ),

                    # PATROL CONTROL STATION
                    html.Div(
                        style=card_style(),
                        children=[
                            section_title("Patrol Planner"),
                            html.H5("Select Police Force Area Jurisdiction", style={"margin": "0 0 8px 0", "color": "#2c3e50"}),
                            dcc.Dropdown(
                                id="pfa-dropdown",
                                options=[{"label": pfa, "value": pfa} for pfa in sorted(PFA_DATA.keys())],
                                value=list(PFA_DATA.keys())[0],
                                clearable=False,
                                style={"marginBottom": "15px"}
                            ),
                            html.H5("Select Operational Origin Node (Start LSOA)", style={"margin": "0 0 8px 0", "color": "#2c3e50"}),
                            dcc.Dropdown(
                                id="start-lsoa-dropdown",
                                placeholder="Select starting LSOA",
                                style={"marginBottom": "15px"}
                            ),
                            html.H5("Patrol Shift Duration Coverage (Number of Node Visits)", style={"margin": "0 0 8px 0", "color": "#2c3e50"}),
                            dcc.Input(
                                id="patrol-length",
                                type="number",
                                min=1,
                                value=10,
                                placeholder="Number of stops",
                                style={"width": "100%", "padding": "8px", "marginBottom": "15px", "borderRadius": "6px", "border": "1px solid #ccc"}
                            ),
                            html.Button(
                                "Generate Patrol",
                                id="generate-patrol-map",
                                n_clicks=0,
                                style={"padding": "12px 20px", "backgroundColor": "#245c97", "color": "white", "border": "none", "borderRadius": "8px", "fontWeight": "bold", "cursor": "pointer"}
                            ),
                            dl.Map(
                                center=[51.5074, -0.1278],
                                zoom=13,
                                style={"width": "100%", "height": "600px"},
                                children=[
                                    dl.TileLayer(),
                                    dl.Polyline(
                                        id="trail-line",
                                        positions=[],
                                        color="blue",
                                        weight=5,
                                    ),
                                ],
                            ),
                            html.Button(
                                "Show patrol as json",
                                id="generate-button",
                                n_clicks=0,
                                style={"padding": "12px 20px", "backgroundColor": "#245c97", "color": "white", "border": "none", "borderRadius": "8px", "fontWeight": "bold", "cursor": "pointer"}
                            ),
                            html.Div(id="pfa-info"),
                            html.Div(id="patrol-output", style={"marginTop": "15px", "backgroundColor": "#f8fafc", "border": "1px solid #e2e8f0", "borderRadius": "8px"})
                        ]
                    ),

                    # CCTV PRIORITY REPORT CARD
                    html.Div(
                        style=card_style(),
                        children=[
                            section_title("Selected LSOAs Ranked by CCTV Priority"),
                            dash_table.DataTable(
                                id="cctv-priority-table",
                                page_size=10,
                                sort_action="native",
                                filter_action="native",
                                sort_mode="multi",
                                style_table={"overflowX": "auto", "borderRadius": "12px", "overflow": "hidden"},
                                style_header={"backgroundColor": "#eef4fb", "fontWeight": "bold", "border": "1px solid #dbe3ef", "color": "#172033", "fontSize": "14px"},
                                style_cell={"textAlign": "left", "padding": "11px", "fontFamily": "Arial, sans-serif", "fontSize": "13px", "border": "1px solid #edf1f7", "color": "#263244", "minWidth": "120px", "maxWidth": "360px", "whiteSpace": "normal"},
                                style_data_conditional=[{"if": {"row_index": "odd"}, "backgroundColor": "#fafcff"}]
                            )
                        ]
                    )
                ]
            )
        ]
    )