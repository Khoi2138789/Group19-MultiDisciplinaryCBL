from dash import Input, Output, State, dash, ctx, Patch
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import json
from dash import html
from data import load_and_prepare_data
GDF_MASTER, DF_FORECAST, DF_HISTORICAL, CRIME_AXES, MOMENTUM_AXES, BAKED_GEOJSON = load_and_prepare_data()
from layout import PFA_DATA
from Patrol.graph import Graph, Node
from Patrol.path import Path
from Patrol.walker import Walker

walked_path = []
trail = []

def register_callbacks(app):

    @app.callback(
        Output("url", "href"),
        Input("reset-btn", "n_clicks"),
        prevent_initial_call=True
    )
    def reset_dashboard(n):
        if n > 0:
            return "/"
        return dash.no_update

    @app.callback(
        Output("selected-lsoas", "data"),
        Input("interactive-map", "selectedData"),
        Input("pcp-graph", "restyleData"),
        Input("distribution-boxplot", "selectedData"),
        State("selected-lsoas", "data"),
        State("pcp-mode-toggle", "value"),
        State("month-slider", "value"),
        prevent_initial_call=True
    )
    def update_global_selection(map_selection, pcp_restyle, boxplot_selection, current_lsoas, pcp_mode, month_value):
        trigger = ctx.triggered_id

        if trigger in ["interactive-map", "distribution-boxplot"]:
            selection_data = map_selection if trigger == "interactive-map" else boxplot_selection
            if selection_data and "points" in selection_data:
                return [pt["customdata"][0] for pt in selection_data["points"]]
            return []

        elif trigger == "pcp-graph":
            if not pcp_restyle or not pcp_restyle[0]:
                return dash.no_update

            df_filtered = GDF_MASTER[GDF_MASTER["LSOA_ID"].isin(current_lsoas)] if current_lsoas else GDF_MASTER.copy()
            df_filtered = df_filtered.reset_index(drop=True)

            df_month = DF_FORECAST[pd.to_datetime(DF_FORECAST["ds"]).dt.month == month_value]
            month_yhat = df_month.groupby("LSOA_ID")["yhat"].mean().reset_index()
            month_yhat.rename(columns={"yhat": "target_month_yhat"}, inplace=True)
            df_filtered = df_filtered.merge(month_yhat, on="LSOA_ID", how="left").fillna(0)

            active_columns = MOMENTUM_AXES + ["target_month_yhat"] if pcp_mode == "momentum" else CRIME_AXES + ["target_month_yhat"]
            changes = pcp_restyle[0]

            for key, value in changes.items():
                if "constraintrange" in key:
                    dim_index = int(key.split("[")[1].split("]")[0])
                    if dim_index < len(active_columns):
                        col_name = active_columns[dim_index]
                        if value:
                            v = value[0] if isinstance(value[0], list) else [value]
                            mask = pd.Series(False, index=df_filtered.index)
                            for r in v:
                                if len(r) == 2:
                                    mask = mask | ((df_filtered[col_name] >= r[0]) & (df_filtered[col_name] <= r[1]))
                            df_filtered = df_filtered[mask]

            return df_filtered["LSOA_ID"].tolist()
        return dash.no_update

    @app.callback(
        Output("interactive-map", "figure"),
        Input("map-view-toggle", "value"),
        Input("month-slider", "value"),
        Input("selected-lsoas", "data"),
        prevent_initial_call=True
    )
    def update_map(view_mode, month_value, selected_lsoas):
        patched_map = Patch()
        trigger = ctx.triggered_id

        if trigger in ["map-view-toggle", "month-slider"] or trigger is None:
            month_str = f"0{month_value}"
            if view_mode == "severity":
                color_col = f"z_score_{month_str}"
                patched_map["data"][0]["z"] = GDF_MASTER[color_col]
                patched_map["data"][0]["colorscale"] = "RdBu_r"
                patched_map["data"][0]["cmin"] = -3
                patched_map["data"][0]["cmax"] = 3
            else:
                if "uncertainty" not in GDF_MASTER.columns:
                    GDF_MASTER["uncertainty"] = GDF_MASTER["yhat_upper"] - GDF_MASTER["yhat_lower"]
                patched_map["data"][0]["z"] = GDF_MASTER["uncertainty"]
                patched_map["data"][0]["colorscale"] = "Purples"
                patched_map["data"][0]["cmin"] = GDF_MASTER["uncertainty"].min()
                patched_map["data"][0]["cmax"] = GDF_MASTER["uncertainty"].max()

        if trigger == "selected-lsoas" or selected_lsoas:
            if selected_lsoas:
                selected_set = set(selected_lsoas)
                selected_indices = [i for i, lsoa in enumerate(GDF_MASTER["LSOA_ID"]) if lsoa in selected_set]
                patched_map["data"][0]["selectedpoints"] = selected_indices
            else:
                patched_map["data"][0]["selectedpoints"] = None
        return patched_map

    @app.callback(
        Output("distribution-boxplot", "figure"),
        Input("selected-lsoas", "data"),
        Input("month-slider", "value")
    )
    def update_distribution(selected_lsoas, month_value):
        df_month = DF_FORECAST[pd.to_datetime(DF_FORECAST["ds"]).dt.month == month_value].copy()
        df_month.rename(columns={"yhat": "Predicted Crime Intensity Score"}, inplace=True)
        plot_df = df_month[df_month["LSOA_ID"].isin(selected_lsoas)] if selected_lsoas else df_month

        if plot_df.empty:
            return go.Figure().update_layout(template="simple_white", title="No data", paper_bgcolor="white", plot_bgcolor="white")

        point_mode = "all" if selected_lsoas and len(selected_lsoas) <= 500 else "outliers"
        fig = go.Figure()
        fig.add_trace(go.Box(
            y=plot_df["Predicted Crime Intensity Score"], customdata=plot_df[["LSOA_ID"]],
            boxpoints=point_mode, marker=dict(size=4, opacity=0.45), line=dict(width=1.5),
            fillcolor="rgba(36, 92, 151, 0.12)", name="", hoveron="points",
            hovertemplate="Area code: %{customdata[0]}<br>Predicted intensity: %{y:,.2f}<extra></extra>"
        ))
        fig.update_layout(
            template="simple_white", margin=dict(l=55, r=25, t=20, b=35), dragmode="select",
            uirevision="constant", paper_bgcolor="white", plot_bgcolor="white",
            font=dict(family="Arial", size=12, color="#1f2d3d"), yaxis_title="Predicted Intensity",
            showlegend=False, hovermode="closest"
        )
        fig.update_yaxes(gridcolor="#edf1f7", zerolinecolor="#dfe6ef", tickformat=",.0f")
        fig.update_xaxes(showticklabels=False)
        return fig

    @app.callback(
        Output("details-datatable", "data"),
        Output("details-datatable", "columns"),
        Input("selected-lsoas", "data"),
        Input("selected-time-window", "data")
    )
    def update_table(selected_lsoas, time_window):
        plot_df = GDF_MASTER[GDF_MASTER["LSOA_ID"].isin(selected_lsoas)] if selected_lsoas else GDF_MASTER

        if time_window:
            start_date, end_date = time_window
            df_hist = DF_HISTORICAL.copy()
            df_hist["Date"] = pd.to_datetime(df_hist["Month"])
            mask = (df_hist["Date"] >= start_date) & (df_hist["Date"] <= end_date)
            if selected_lsoas:
                mask = mask & (df_hist["LSOA_ID"].isin(selected_lsoas))

            filtered_df = df_hist[mask].groupby("LSOA_ID")["Total_CII_Score"].mean().reset_index()
            filtered_df.rename(columns={"Total_CII_Score": "Intensity"}, inplace=True)
            name_map = GDF_MASTER[["LSOA_ID", "LSOA_NAME"]].drop_duplicates().reset_index(drop=True)
            filtered_df = filtered_df.merge(name_map, on="LSOA_ID")
            display_cols = ["LSOA_NAME", "LSOA_ID", "Intensity"]
        else:
            filtered_df = plot_df.rename(
                columns={"yhat": "Predicted Crime Intensity Score", "yhat_lower": "Lower Certainty Bound",
                         "yhat_upper": "Upper Certainty Bound"})
            display_cols = ["LSOA_NAME", "LSOA_ID", "Predicted Crime Intensity Score", "Lower Certainty Bound",
                            "Upper Certainty Bound"]

        filtered_df = filtered_df[display_cols].round(2)
        pretty_names = {"LSOA_NAME": "Area Name", "LSOA_ID": "Area Code",
                        "Predicted Crime Intensity Score": "Predicted Intensity",
                        "Lower Certainty Bound": "Lower Bound", "Upper Certainty Bound": "Upper Bound",
                        "Intensity": "Historical Intensity"}

        columns = []
        for col in display_cols:
            if col in ["LSOA_NAME", "LSOA_ID"]:
                columns.append({"name": pretty_names.get(col, col), "id": col, "type": "text"})
            else:
                columns.append(
                    {"name": pretty_names.get(col, col), "id": col, "type": "numeric", "format": {"specifier": ",.2f"}})
        return filtered_df.to_dict("records"), columns

    @app.callback(
        Output("pcp-graph", "figure"),
        Input("pcp-mode-toggle", "value"),
        Input("selected-lsoas", "data"),
        Input("month-slider", "value")
    )
    def update_pcp(mode, selected_lsoas, month_value):
        if GDF_MASTER is None or GDF_MASTER.empty:
            return go.Figure().update_layout(template="simple_white", title="Loading...")

        plot_df = GDF_MASTER[GDF_MASTER["LSOA_ID"].isin(selected_lsoas)].reset_index(
            drop=True) if selected_lsoas else GDF_MASTER.copy().reset_index(drop=True)
        df_month = DF_FORECAST[pd.to_datetime(DF_FORECAST["ds"]).dt.month == month_value]
        month_yhat = df_month.groupby("LSOA_ID")["yhat"].mean().reset_index()
        month_yhat.rename(columns={"yhat": "target_month_yhat"}, inplace=True)

        plot_df = plot_df.merge(month_yhat, on="LSOA_ID", how="left").replace([np.inf, -np.inf], 0).fillna(0)
        axes = MOMENTUM_AXES + ["target_month_yhat"] if mode == "momentum" else CRIME_AXES + ["target_month_yhat"]

        if not selected_lsoas and len(plot_df) > 5000:
            plot_df = plot_df.sample(n=5000, random_state=42)

        dimensions = []
        for col in axes:
            max_val = plot_df[col].quantile(0.98)
            label_text = f"Predicted {month_value}/2026" if col == "target_month_yhat" else str(col)
            dimensions.append(dict(label=label_text, values=plot_df[col], range=[0, max(max_val, 1)]))

        N = len(axes)
        bottom_labels = []
        for i, col in enumerate(axes):
            label_text = f"Predicted {month_value}/2026" if col == "target_month_yhat" else str(col)
            x_pos = i / (N - 1) if N > 1 else 0.5
            bottom_labels.append(dict(
                x=x_pos, y=0.06,
                xref="paper", yref="paper",
                text=label_text,
                showarrow=False,
                font=dict(size=11, color="#1f2d3d", family="Arial"),
                xanchor="center", yanchor="top"
            ))

        fig = go.Figure(data=go.Parcoords(
            line=dict(color=plot_df["target_month_yhat"], colorscale="Reds", showscale=False),
            dimensions=dimensions, labelfont=dict(size=12, color="#1f2d3d"), tickfont=dict(size=10, color="#334155"),
            domain={"y": [0.18, 1.0]}
        ))
        fig.update_layout(margin=dict(l=35, r=35, t=20, b=50), paper_bgcolor="white", plot_bgcolor="white",
                          font=dict(family="Arial", size=12, color="#1f2d3d"), annotations=bottom_labels)
        return fig

    @app.callback(
        Output("timeseries-graph", "figure"),
        Input("selected-lsoas", "data")
    )
    def update_timeseries(selected_lsoas):
        hist_df = DF_HISTORICAL[DF_HISTORICAL["LSOA_ID"].isin(selected_lsoas)] if selected_lsoas else DF_HISTORICAL
        fore_df = DF_FORECAST[DF_FORECAST["LSOA_ID"].isin(selected_lsoas)] if selected_lsoas else DF_FORECAST

        hist_agg = hist_df.groupby("Month")["Total_CII_Score"].mean().reset_index()
        fore_agg = fore_df.groupby("ds")[["yhat", "yhat_lower", "yhat_upper"]].mean().reset_index()

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist_agg["Month"], y=hist_agg["Total_CII_Score"], mode="lines", name="Historical baseline", line=dict(width=2.5), hovertemplate="Historical intensity: %{y:,.0f}<extra></extra>"))
        fig.add_trace(go.Scatter(x=fore_agg["ds"], y=fore_agg["yhat"], mode="lines", name="Forecast", line=dict(width=2.5), hovertemplate="Predicted intensity: %{y:,.0f}<extra></extra>"))
        fig.update_layout(
            template="simple_white", hovermode="x unified", margin=dict(l=55, r=25, t=20, b=40),
            yaxis_title="Intensity Score", paper_bgcolor="white", plot_bgcolor="white",
            font=dict(family="Arial", size=12, color="#1f2d3d"), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        fig.update_yaxes(gridcolor="#edf1f7", zerolinecolor="#dfe6ef")
        fig.update_xaxes(gridcolor="#edf1f7")
        return fig

    @app.callback(
        Output("selected-time-window", "data"),
        Input("timeseries-graph", "relayoutData")
    )
    def update_time_filter(relayout_data):
        if relayout_data and "xaxis.range[0]" in relayout_data:
            return [relayout_data["xaxis.range[0]"], relayout_data["xaxis.range[1]"]]
        return None

    @app.callback(
        Output("cctv-priority-table", "data"),
        Output("cctv-priority-table", "columns"),
        Input("selected-lsoas", "data")
    )
    def update_cctv_priority_table(selected_lsoas):
        filtered_df = GDF_MASTER[GDF_MASTER["LSOA_ID"].isin(selected_lsoas)].copy() if selected_lsoas else GDF_MASTER.copy()
        display_cols = ["LSOA_NAME", "LSOA_ID", "unsolved_non_severe", "total_non_severe", "priority_level", "cctv_score", "cctv_rank"]

        filtered_df = filtered_df[display_cols].copy()
        filtered_df = filtered_df[filtered_df["cctv_score"] > 0].sort_values(by=["cctv_rank", "cctv_score"], ascending=[True, False])
        if not selected_lsoas:
            filtered_df = filtered_df.head(100)

        filtered_df = filtered_df.rename(columns={
            "LSOA_NAME": "LSOA name", "LSOA_ID": "LSOA code", "unsolved_non_severe": "Unsolved non-severe crimes",
            "total_non_severe": "Total non-severe crimes", "priority_level": "Priority level",
            "cctv_score": "CCTV score", "cctv_rank": "Priority installation rank"
        })
        return filtered_df.round(2).to_dict("records"), [{"name": col, "id": col} for col in filtered_df.columns]

    @app.callback(
        Output("start-lsoa-dropdown", "options"),
        Output("start-lsoa-dropdown", "value"),
        Input("pfa-dropdown", "value")
    )
    def update_lsoa_dropdown(selected_pfa):
        lsoas = PFA_DATA[selected_pfa]
        options = [{"label": f"{lsoa['lsoa_name']} ({lsoa['lsoa_code']})", "value": lsoa["lsoa_code"]} for lsoa in lsoas]
        return options, (options[0]["value"] if options else None)

    @app.callback(
        Output("patrol-output", "children"),
        Input("generate-button", "n_clicks"),
        State("pfa-dropdown", "value"),
        State("start-lsoa-dropdown", "value"),
        State("patrol-length", "value"),
        prevent_initial_call=True
    )
    def generate_patrol(n_clicks, selected_pfa, start_lsoa, patrol_length):
        print("generating patrol network graph json")

        return html.Pre(json.dumps(walked_path, indent=2))

    @app.callback(
        Output("trail-line", "positions"),
        Input("generate-patrol-map", "n_clicks"),
        State("pfa-dropdown", "value"),
        State("start-lsoa-dropdown", "value"),
        State("patrol-length", "value"),
        State("patrol-month-dropdown", "value"),
        prevent_initial_call=True,
    )

    def show_trail(n_clicks, selected_pfa, start_lsoa, patrol_length, selected_month):

        print(f"generating patrol network graph map for month: {selected_month}")
        graph = Graph()
        nodes_by_id = {}
        lsoas = PFA_DATA[selected_pfa]

        for item in lsoas:
            z_score_val = item["all_z_scores"].get(selected_month, 0)

            node = Node(
                _id=item["lsoa_code"],
                value=1 / (1 + np.exp(-z_score_val)),
                lat=item["lat"],
                lon=item["lon"]
            )
            graph.add_node(node)
            nodes_by_id[node.id] = node

        pfa_lsoas = set(item["lsoa_code"] for item in lsoas)
        for item in lsoas:
            source = nodes_by_id[item["lsoa_code"]]
            for nid in item["neighbours"]:
                if nid not in pfa_lsoas:
                    continue
                target = nodes_by_id[nid]
                graph.add_edge(source, target)

        path = Path(memory=5)
        walker = Walker(graph, path)
        start = nodes_by_id[start_lsoa]
        walker.set_start(start)

        global walked_path
        walked_path = [{"lsoa": start.id, "lat": start.lat, "lon": start.lon}]
        for _ in range(patrol_length):
            nxt = walker.step_random()
            walked_path.append({"lsoa": nxt.id, "lat": nxt.lat, "lon": nxt.lon})

        global trail
        trail = [[point["lat"], point["lon"]] for point in walked_path]
        return trail