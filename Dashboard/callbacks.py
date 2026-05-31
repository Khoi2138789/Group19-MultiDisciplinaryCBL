from dash import Input, Output, State, dash, ctx, Patch
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

from data import GDF_MASTER, DF_FORECAST, DF_HISTORICAL, CRIME_AXES, MOMENTUM_AXES


def register_callbacks(app):
    @app.callback(
        Output('url', 'href'),
        Input('reset-btn', 'n_clicks'),
        prevent_initial_call=True
    )
    def reset_dashboard(n):
        if n > 0: return '/'
        return dash.no_update

    @app.callback(
        Output("selected-lsoas", "data"),
        Input("interactive-map", "selectedData"),
        Input("pcp-graph", "restyleData"),
        Input("distribution-boxplot", "selectedData"),  # NEW: Listen to the boxplot lasso!
        State("selected-lsoas", "data"),
        State("pcp-mode-toggle", "value"),
        State("month-slider", "value"),
        prevent_initial_call=True
    )
    def update_global_selection(map_selection, pcp_restyle, boxplot_selection, current_lsoas, pcp_mode, month_value):
        trigger = ctx.triggered_id

        # 1. MAP OR BOXPLOT BRUSHING
        # Because we added custom_data to the boxplot, the extraction logic is identical
        if trigger in ["interactive-map", "distribution-boxplot"]:
            # Figure out which graph the user actually touched
            selection_data = map_selection if trigger == "interactive-map" else boxplot_selection

            if selection_data and 'points' in selection_data:
                return [pt['customdata'][0] for pt in selection_data['points']]
            return []

        # 2. PCP FILTERING
        elif trigger == "pcp-graph":
            if not pcp_restyle or not pcp_restyle[0]: return dash.no_update

            df_filtered = GDF_MASTER[GDF_MASTER['LSOA_ID'].isin(current_lsoas)] if current_lsoas else GDF_MASTER.copy()

            # --- THE FIX ---
            # Strip the ambiguous index label before merging
            df_filtered = df_filtered.reset_index(drop=True)

            # Calculate the specific month's yhat on the fly for filtering
            df_month = DF_FORECAST[pd.to_datetime(DF_FORECAST['ds']).dt.month == month_value]
            month_yhat = df_month.groupby('LSOA_ID')['yhat'].mean().reset_index()
            month_yhat.rename(columns={'yhat': 'target_month_yhat'}, inplace=True)

            df_filtered = df_filtered.merge(month_yhat, on='LSOA_ID', how='left').fillna(0)

            active_columns = MOMENTUM_AXES + ['target_month_yhat'] if pcp_mode == 'momentum' else CRIME_AXES + [
                'target_month_yhat']
            changes = pcp_restyle[0]

            for key, value in changes.items():
                if "constraintrange" in key:
                    dim_index = int(key.split('[')[1].split(']')[0])
                    if dim_index < len(active_columns):
                        col_name = active_columns[dim_index]
                        if value:
                            v = value[0]
                            if not isinstance(v[0], list): v = [v]
                            mask = pd.Series(False, index=df_filtered.index)
                            for r in v:
                                if len(r) == 2: mask = mask | (
                                        (df_filtered[col_name] >= r[0]) & (df_filtered[col_name] <= r[1]))
                            df_filtered = df_filtered[mask]
            return df_filtered['LSOA_ID'].tolist()

        return dash.no_update
    @app.callback(
        Output("interactive-map", "figure"),
        Input("map-view-toggle", "value"),
        Input("month-slider", "value"),
        Input("selected-lsoas", "data"),
        prevent_initial_call=True  # CRITICAL: Prevents overwriting the pre-compiled map on startup
    )
    def update_map(view_mode, month_value, selected_lsoas):
        # Initialize the Dash Sniper Tool (Patch)
        patched_map = Patch()

        # 1. Figure out what triggered the update
        trigger = ctx.triggered_id

        # 2. IF THE SLIDER OR TOGGLE MOVED: Update the colors!
        if trigger in ["map-view-toggle", "month-slider"] or trigger is None:
            month_str = f"0{month_value}"

            if view_mode == 'severity':
                color_col = f'z_score_{month_str}'

                # We only send the new Z-Scores and the color rules to the browser
                patched_map['data'][0]['z'] = GDF_MASTER[color_col]
                patched_map['data'][0]['colorscale'] = "RdBu_r"
                patched_map['data'][0]['cmin'] = -3
                patched_map['data'][0]['cmax'] = 3
            else:
                # Calculate uncertainty on the fly if needed
                if 'uncertainty' not in GDF_MASTER.columns:
                    GDF_MASTER['uncertainty'] = GDF_MASTER['yhat_upper'] - GDF_MASTER['yhat_lower']

                patched_map['data'][0]['z'] = GDF_MASTER['uncertainty']
                patched_map['data'][0]['colorscale'] = "Purples"
                patched_map['data'][0]['cmin'] = GDF_MASTER['uncertainty'].min()
                patched_map['data'][0]['cmax'] = GDF_MASTER['uncertainty'].max()

        # 3. IF THE USER BRUSHED/FILTERED: Update the dimming!
        if trigger == "selected-lsoas" or selected_lsoas:
            if selected_lsoas:
                # Plotly needs the exact row numbers (indices) to highlight them.
                # This perfectly matches the order of GDF_MASTER used to compile the map.
                selected_indices = [i for i, lsoa in enumerate(GDF_MASTER['LSOA_ID']) if lsoa in selected_lsoas]
                patched_map['data'][0]['selectedpoints'] = selected_indices
            else:
                # If they clear the filter, clear the dimming (set to None)
                patched_map['data'][0]['selectedpoints'] = None

        return patched_map

    @app.callback(
        Output("distribution-boxplot", "figure"),
        Input("selected-lsoas", "data"),
        Input("month-slider", "value")
    )
    def update_distribution(selected_lsoas, month_value):
        df_month = DF_FORECAST[pd.to_datetime(DF_FORECAST['ds']).dt.month == month_value].copy()

        # RENAME FOR CLEAN HOVER TEXT
        df_month.rename(columns={'yhat': 'Predicted Crime Intensity Score'}, inplace=True)

        plot_df = df_month[df_month['LSOA_ID'].isin(selected_lsoas)] if selected_lsoas else df_month

        if plot_df.empty:
            return go.Figure().update_layout(template="simple_white", title="No data")

        fig = px.box(plot_df, y='Predicted Crime Intensity Score', points="all", template="simple_white",
                     custom_data=['LSOA_ID'])
        fig.update_yaxes(type="linear")

        # THE FIX: uirevision='constant' prevents the plot from resetting its lasso selection when redrawn
        fig.update_layout(
            margin=dict(l=40, r=20, t=40, b=20),
            dragmode='select',
            uirevision='constant'
        )
        return fig

    @app.callback(
        Output("details-datatable", "data"),
        Output("details-datatable", "columns"),
        Input("selected-lsoas", "data"),
        Input("selected-time-window", "data")
    )
    def update_table(selected_lsoas, time_window):
        plot_df = GDF_MASTER[GDF_MASTER['LSOA_ID'].isin(selected_lsoas)] if selected_lsoas else GDF_MASTER.sort_values(
            'yhat', ascending=False).head(100)

        if time_window:
            start_date, end_date = time_window
            DF_HISTORICAL['Date'] = pd.to_datetime(DF_HISTORICAL['Month'])
            mask = (DF_HISTORICAL['Date'] >= start_date) & (DF_HISTORICAL['Date'] <= end_date)
            if selected_lsoas: mask = mask & (DF_HISTORICAL['LSOA_ID'].isin(selected_lsoas))
            filtered_df = DF_HISTORICAL[mask].groupby('LSOA_ID')['Total_CII_Score'].mean().reset_index()
            filtered_df.rename(columns={'Total_CII_Score': 'Intensity'}, inplace=True)
            name_map = GDF_MASTER[['LSOA_ID', 'LSOA_NAME']].drop_duplicates().reset_index(drop=True)
            filtered_df = filtered_df.merge(name_map, on='LSOA_ID')
            display_cols = ['LSOA_NAME', 'LSOA_ID', 'Intensity']
        else:
            # RENAME COLUMNS FOR THE UI
            filtered_df = plot_df.rename(columns={
                'yhat': 'Predicted Crime Intensity Score',
                'yhat_lower': 'Lower Certainty Bound',
                'yhat_upper': 'Upper Certainty Bound'
            })
            display_cols = ['LSOA_NAME', 'LSOA_ID', 'Predicted Crime Intensity Score', 'Lower Certainty Bound',
                            'Upper Certainty Bound']

        return filtered_df[display_cols].round(2).to_dict('records'), [{"name": i, "id": i} for i in display_cols]

    @app.callback(
        Output("pcp-graph", "figure"),
        Input("pcp-mode-toggle", "value"),
        Input("selected-lsoas", "data"),
        Input("month-slider", "value")  # NEW: Listen to the slider
    )
    def update_pcp(mode, selected_lsoas, month_value):
        if GDF_MASTER is None or GDF_MASTER.empty:
            return go.Figure().update_layout(template="simple_white", title="Loading...")

        plot_df = GDF_MASTER[GDF_MASTER['LSOA_ID'].isin(selected_lsoas)] if selected_lsoas else GDF_MASTER.copy()
        # --- THE FIX ---
        # Strip the ambiguous index label before merging
        plot_df = plot_df.reset_index(drop=True)

        # Merge the specific month's prediction to color the lines correctly
        df_month = DF_FORECAST[pd.to_datetime(DF_FORECAST['ds']).dt.month == month_value]
        month_yhat = df_month.groupby('LSOA_ID')['yhat'].mean().reset_index()
        month_yhat.rename(columns={'yhat': 'target_month_yhat'}, inplace=True)

        plot_df = plot_df.merge(month_yhat, on='LSOA_ID', how='left')
        plot_df['target_month_yhat'] = plot_df['target_month_yhat'].fillna(0)
        plot_df = plot_df.replace([np.inf, -np.inf], 0).fillna(0)

        # Decide which axes to show. Add the target month prediction to the end of BOTH modes!
        axes = MOMENTUM_AXES + ['target_month_yhat'] if mode == 'momentum' else CRIME_AXES + ['target_month_yhat']
        dimensions = []

        for col in axes:
            max_val = plot_df[col].quantile(0.98)
            # Make the axis label readable in the UI
            label_text = f"Predicted (Month {month_value})" if col == 'target_month_yhat' else str(col)
            dimensions.append(dict(label=label_text, values=plot_df[col], range=[0, max(max_val, 1)]))

        fig = go.Figure(data=go.Parcoords(
            line=dict(color=plot_df['target_month_yhat'], colorscale='Reds'),
            dimensions=dimensions
        ))
        fig.update_layout(margin=dict(l=40, r=40, t=40, b=20), paper_bgcolor="white")
        return fig

    @app.callback(
        Output("timeseries-graph", "figure"),
        Input("selected-lsoas", "data")
    )
    def update_timeseries(selected_lsoas):
        hist_df = DF_HISTORICAL[DF_HISTORICAL['LSOA_ID'].isin(selected_lsoas)] if selected_lsoas else DF_HISTORICAL
        fore_df = DF_FORECAST[DF_FORECAST['LSOA_ID'].isin(selected_lsoas)] if selected_lsoas else DF_FORECAST

        hist_agg = hist_df.groupby('Month')['Total_CII_Score'].mean().reset_index()
        fore_agg = fore_df.groupby('ds')[['yhat', 'yhat_lower', 'yhat_upper']].mean().reset_index()

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist_agg['Month'], y=hist_agg['Total_CII_Score'], mode='lines', name='Baseline'))

        # ADDED HOVER TEMPLATE HERE
        fig.add_trace(go.Scatter(
            x=fore_agg['ds'],
            y=fore_agg['yhat'],
            mode='lines',
            name='Forecast',
            hovertemplate='Predicted Crime Intensity Score: %{y:.2f}<extra></extra>'
        ))

        fig.update_layout(
            template="simple_white",
            hovermode="x unified",
            margin=dict(l=40, r=20, t=40, b=20),
            xaxis=dict(rangeslider=dict(visible=False)),
            yaxis_title="Intensity Score"
        )
        return fig

    @app.callback(
        Output("selected-time-window", "data"),
        Input("timeseries-graph", "relayoutData")
    )
    def update_time_filter(relayout_data):
        if relayout_data and 'xaxis.range[0]' in relayout_data:
            return [relayout_data['xaxis.range[0]'], relayout_data['xaxis.range[1]']]
        return None