import glob
import dash
from dash import Dash, html, dcc, callback, Output, Input, State, Patch, register_page
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import json
import h5py
from flask import current_app, session
import sys

from general_functions import *
from .dataset_cache import dataset_cache
from index_string import index_string

from common_explorer import protect_dashviews, generate_basic_components, add_common_callbacks


def add_dash(server, env):


    dashapp = dash.Dash(__name__, 
                        server = server, 
                        use_pages = False, 
                        url_base_pathname = f"/datasets/hyperspectra_viewer/", 
                        external_stylesheets=[dbc.themes.BOOTSTRAP], 
                        suppress_callback_exceptions = True)

    dashapp.index_string = index_string

    basic_layout = generate_basic_components("Hyperspectral Explorer", reload_interval = 600, one_or_more = "one", kw_suggestion = "hyperspec") # check for new datasets every 10 min, default = 45 sec

    #  ================================= HYPERSPECTRAL SPECIFIC =========================
    additional_app_components = [   html.H5(id = 'info', children = "Currently showing:", style = {'margin-top':'50px', 'margin-bottom':'10px'}),
                                    html.Div(id = 'dataset-name', style={'width': '100%', 'margin-bottom': '10px'}),
                                    html.Div(id = 'dataset-id', style={'width': '100%', 'margin-bottom': '30px'}),
                                    html.H3("Spectral Map (avg per pixel)"),
                                    dcc.Graph(id='fig1', figure = ""),
                                    html.Div(id = "fig1-info"),
                                    html.H3("Spectra"),
                                    html.P("Hover over spectral map to see spectra at a given pixel"),
                                    dcc.Graph(id='fig2', figure = ""), # reacts to figure 1 - initial call prevented
                                    html.H1(id="hover-text", children="..."), # reacts to figure 1 - initially Null
                                ]
    #  ================================= // ================== // =========================
    
    dashapp.layout = dbc.Container(
                                   basic_layout + additional_app_components, 
                                   fluid=True, 
                                   style={"margin": "0 auto", "max-width": "80%"}
                                  )

    #protect_dashviews(dashapp)
    add_common_callbacks(dashapp, env) 
   
    #  ================================= HYPERSPECTRAL SPECIFIC CALLBACKS =========================
    @dashapp.callback(
        Output(component_id='fig1', component_property='figure'),
        Output(component_id='dataset-name', component_property='children'),
        Output(component_id='dataset-id', component_property='children'),
        Input("auth-var", "value"),
        Input("url", "pathname"),
        Input("kw-checklist", "value"),
        Input("fig2", "selectedData"))
    def gen_fig1(auth, url_path, dsvalue, selectedData):
        if auth is None:
            raise PreventUpdate
        else:
            print(f"fig1: {dsvalue}")
            dsid = dsvalue.strip('"').strip("'")

            print(f"checking for {dsid} in cache")
            dataset_cache(dsid, config=current_app.config, always_sync=False)

            print(f"{current_app.config=}")

            dsname = glob.glob(f"./assets/{dsid}/*.h5")[-1]
            with h5py.File(dsname, 'r') as f:
                M = f['measurement/hyperspec_picam_mcl']
                spec_map = np.array(M['spec_map'])[0]
                h_array = np.array(M['h_array'])
                v_array = np.array(M['v_array'])
                wls = np.array(M['wls'])
            print(f'selected-data {selectedData}')
            if selectedData is None:
                im = spec_map.mean(axis=-1)
            else:
                kk0,kk1 = np.searchsorted(wls, selectedData["range"]["x"])
                im = spec_map[:,:,kk0:kk1].max(axis=-1)
                print(f"got kk0, kk1, and new im: {kk0}, {kk1}, {im}")
                
            fig = go.FigureWidget()
            imshow = fig.add_heatmap(z=im,x=h_array,y=v_array)
            fig.update_yaxes(scaleanchor="x", scaleratio=1)
            return(fig, f"Dataset: {dsname}", f"Dataset ID: {dsid}")
            


    @dashapp.callback(
        Output(component_id='fig2', component_property='figure'),
        Input("auth-var", "value"),
        Input("url", "pathname"),
        Input("kw-checklist", "value"),
        Input(component_id = 'fig1', component_property = 'hoverData')) 
    def gen_fig2(auth, url_path, dsvalue, hoverData):
        if auth is None:
            raise PreventUpdate
        else:
            print(f"fig2: {dsvalue}")
            dsid = dsvalue.strip('"').strip("'")

            print(f"checking for {dsid} in cache")
            dataset_cache(dsid, config=current_app.config, always_sync=False)

            dsname = glob.glob(f"./assets/{dsid}/*.h5")[-1]
            print(dsname)
            with h5py.File(dsname, 'r') as f:
                M = f['measurement/hyperspec_picam_mcl']
                h_array = np.array(M['h_array'])
                v_array = np.array(M['v_array'])
                spec_map = np.array(M['spec_map'])[0]
                wls = np.array(M['wls'])
            if hoverData is None:
                spec_line = go.Figure(data = [go.Scatter(x=wls, 
                                                         y=spec_map[0,0,:],
                                                         mode = "markers+lines", 
                                                         marker=dict(size=2))])
                return(spec_line)
            else:
                pt = hoverData["points"][0]
                x = pt["x"]
                y = pt["y"]
                ii = np.searchsorted(h_array,x)
                jj = np.searchsorted(v_array,y)
                patched_fig = Patch() # Patching requires dash v2.9 or later
                patched_fig["data"][0]["x"] = wls
                patched_fig["data"][0]["y"] = spec_map[jj,ii,:]
                return patched_fig


    @dashapp.callback(
        Output('hover-text', 'children'),
        [Input('fig1', 'hoverData')])
    def display_hoverdata(hoverData):
        return json.dumps(hoverData, indent=2)


    return(server)
