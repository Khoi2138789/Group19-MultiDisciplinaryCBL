import os
import plotly.io as pio
from dash import dcc, html, dash_table

# Locate and load the pre-compiled map instantly when the server starts
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAP_FILE = os.path.join(BASE_DIR, 'precompiled_map.json')

print("Loading pre-compiled map into layout...")
INITIAL_MAP = pio.read_json(MAP_FILE)

# --- NEW OVERRIDES ---
# 1. Kill the hover tooltips entirely so they don't block the colors
INITIAL_MAP.update_traces(hoverinfo='none', hovertemplate=None)

# 2. Change the default mouse drag from 'Pan' to 'Lasso'
INITIAL_MAP.update_layout(dragmode='lasso')


def make_layout():
    return html.Div(
        style={
            "height": "100vh",
            "width": "100vw",
            "display": "flex",
            "flexDirection": "column",
            "fontFamily": "Arial, sans-serif",
            "overflow": "hidden",
            "backgroundColor": "#f4f6f8"
        },
        children=[
            dcc.Location(id='url', refresh=True),
            dcc.Store(id="selected-lsoas", data=[]),
            dcc.Store(id="selected-time-window", data=None),

            # HEADER
            html.Div(
                style={
                    "height": "60px", "display": "flex", "justifyContent": "space-between",
                    "alignItems": "center", "padding": "0 20px", "backgroundColor": "#1e2b3c",
                    "color": "white", "boxShadow": "0 2px 4px rgba(0,0,0,0.1)", "zIndex": 100, "flexShrink": 0
                },
                children=[
                    html.H2("Predictive Crime Intensity & Transparency Explorer",
                            style={"margin": 0, "fontSize": "22px", "fontWeight": "300"}),
                    html.Button("⟳ Reset Filters", id="reset-btn", n_clicks=0,
                                style={"cursor": "pointer", "padding": "8px 16px", "backgroundColor": "transparent",
                                       "color": "white", "border": "1px solid white", "borderRadius": "4px"})
                ]
            ),

            # MAIN WORKSPACE
            html.Div(
                id="main-workspace",
                style={"display": "flex", "flexDirection": "column", "flex": 1, "overflowY": "auto", "padding": "15px",
                       "gap": "15px"},
                children=[

                    # ROW 1: Map Anchor (25%) + PCP (75%)
                    html.Div(
                        style={"display": "flex", "gap": "15px", "height": "400px", "flexShrink": 0},
                        children=[
                            # MAP CONTAINER
                            html.Div(
                                style={"width": "25%", "display": "flex", "flexDirection": "column",
                                       "backgroundColor": "white", "borderRadius": "8px",
                                       "boxShadow": "0 1px 3px rgba(0,0,0,0.05)", "overflow": "hidden"},
                                children=[
                                    html.Div(
                                        style={"padding": "12px", "borderBottom": "1px solid #eee",
                                               "backgroundColor": "#f8f9fa"},
                                        children=[
                                            html.Div([
                                                html.Strong("Spatial Monthly Z-Score & Uncertainty Forecasts",
                                                            style={"marginRight": "10px", "fontSize": "13px"}),
                                                dcc.RadioItems(
                                                    id="map-view-toggle",
                                                    options=[
                                                        {"label": " Severity (Z-Score)", "value": "severity"},
                                                        {"label": " Uncertainty", "value": "uncertainty"}
                                                    ],
                                                    value="severity", inline=True,
                                                    style={"display": "inline-block", "fontSize": "12px"}
                                                )
                                            ]),

                                            # UPDATED: Dropdown instead of Slider
                                            html.Div([
                                                html.Strong("Target Month: ",
                                                            style={"fontSize": "12px", "display": "block",
                                                                   "marginTop": "10px", "marginBottom": "5px"}),
                                                dcc.Dropdown(
                                                    id='month-slider',
                                                    # Keeping the ID so callbacks still work perfectly
                                                    options=[
                                                        {'label': 'April 2026', 'value': 4},
                                                        {'label': 'May 2026', 'value': 5},
                                                        {'label': 'June 2026', 'value': 6},
                                                        {'label': 'July 2026', 'value': 7},
                                                        {'label': 'August 2026', 'value': 8}
                                                    ],
                                                    value=4,
                                                    clearable=False,
                                                    searchable=False,
                                                    style={"fontSize": "13px", "color": "#2c3e50"}
                                                )
                                            ])
                                        ]
                                    ),
                                    # BULLETPROOF MAP WRAPPER
                                    html.Div(
                                        style={"flex": 1, "position": "relative", "minHeight": 0},
                                        children=[
                                            dcc.Graph(
                                                id="interactive-map",
                                                figure=INITIAL_MAP,
                                                responsive=True,
                                                style={"position": "absolute", "top": 0, "left": 0, "width": "100%",
                                                       "height": "100%"},
                                                config={"displayModeBar": True, "scrollZoom": True}
                                            )
                                        ]
                                    )
                                ]
                            ),

                            # PCP CONTAINER
                            html.Div(
                                style={"width": "75%", "display": "flex", "flexDirection": "column",
                                       "backgroundColor": "white", "borderRadius": "8px",
                                       "boxShadow": "0 1px 3px rgba(0,0,0,0.05)", "padding": "15px"},
                                children=[
                                    html.Div(
                                        style={"display": "flex", "justifyContent": "space-between",
                                               "alignItems": "center", "marginBottom": "10px"},
                                        children=[
                                            html.H4("Yearly Historical Averages & Crime Type Totals",
                                                    style={"margin": 0, "color": "#2c3e50"}),
                                            dcc.RadioItems(
                                                id="pcp-mode-toggle",
                                                options=[
                                                    {"label": " Historical Momentum ", "value": "momentum"},
                                                    {"label": " Crime Type Profile ", "value": "type"}
                                                ],
                                                value="momentum", inline=True, style={"fontSize": "13px"}
                                            )
                                        ]
                                    ),
                                    # BULLETPROOF PCP WRAPPER
                                    html.Div(
                                        style={"flex": 1, "position": "relative", "minHeight": 0},
                                        children=[
                                            dcc.Graph(
                                                id="pcp-graph",
                                                responsive=True,
                                                style={"position": "absolute", "top": 0, "left": 0, "width": "100%",
                                                       "height": "100%"},
                                                config={"displayModeBar": False}
                                            )
                                        ]
                                    )
                                ]
                            )
                        ]
                    ),

                    # ROW 2: Boxplot + Time Series
                    html.Div(
                        style={"display": "flex", "gap": "15px", "height": "320px", "flexShrink": 0},
                        children=[
                            # BOXPLOT CONTAINER
                            html.Div(
                                style={"width": "35%", "display": "flex", "flexDirection": "column",
                                       "backgroundColor": "white", "padding": "15px",
                                       "borderRadius": "8px", "boxShadow": "0 1px 3px rgba(0,0,0,0.05)"},
                                children=[
                                    # UPDATED TITLE
                                    html.H4("Monthly Predicted Crime Intensity Distribution",
                                            style={"margin": "0 0 10px 0", "color": "#2c3e50", "fontSize": "16px"}),
                                    # BULLETPROOF BOXPLOT WRAPPER
                                    html.Div(
                                        style={"flex": 1, "position": "relative", "minHeight": 0},
                                        children=[
                                            dcc.Graph(
                                                id="distribution-boxplot",
                                                responsive=True,
                                                style={"position": "absolute", "top": 0, "left": 0, "width": "100%",
                                                       "height": "100%"},
                                                config={"displayModeBar": False}
                                            )
                                        ]
                                    )
                                ]
                            ),

                            # TIMESERIES CONTAINER
                            html.Div(
                                style={"width": "65%", "display": "flex", "flexDirection": "column",
                                       "backgroundColor": "white", "padding": "15px",
                                       "borderRadius": "8px", "boxShadow": "0 1px 3px rgba(0,0,0,0.05)"},
                                children=[
                                    # UPDATED TITLE
                                    html.H4("Historical Monthly Averages & Summer Prediction Trends",
                                            style={"margin": "0 0 10px 0", "color": "#2c3e50", "fontSize": "16px"}),
                                    # BULLETPROOF TIMESERIES WRAPPER
                                    html.Div(
                                        style={"flex": 1, "position": "relative", "minHeight": 0},
                                        children=[
                                            dcc.Graph(
                                                id="timeseries-graph",
                                                responsive=True,
                                                style={"position": "absolute", "top": 0, "left": 0, "width": "100%",
                                                       "height": "100%"},
                                                config={"displayModeBar": False}
                                            )
                                        ]
                                    )
                                ]
                            )
                        ]
                    ),

                    # ROW 3: Data Table
                    html.Div(
                        style={"backgroundColor": "white", "padding": "15px", "borderRadius": "8px",
                               "boxShadow": "0 1px 3px rgba(0,0,0,0.05)", "flexShrink": 0},
                        children=[
                            # UPDATED TITLE
                            html.H4("Granular LSOA Forecasts & Selected Temporal Averages",
                                    style={"margin": "0 0 15px 0", "color": "#2c3e50", "fontSize": "16px"}),
                            dash_table.DataTable(
                                id="details-datatable", page_size=6, sort_action="native", filter_action="native",
                                sort_mode="multi",
                                style_table={"overflowX": "auto"},
                                style_header={"backgroundColor": "#f8f9fa", "fontWeight": "bold",
                                              "border": "1px solid #eee"},
                                style_cell={"textAlign": "left", "padding": "10px", "fontFamily": "Arial, sans-serif",
                                            "fontSize": "13px", "border": "1px solid #eee"}
                            )
                        ]
                    )
                ]
            )
        ]
    )