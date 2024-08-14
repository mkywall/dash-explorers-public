import glob
import dash
from dash import Dash, html, dcc, callback, Output, Input, State, Patch, register_page
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import json
import h5py
from flask import current_app, session
import sys
from general_functions import *
from powerfit import linear, normalize_data, wv_range, custom_function, find_nearest, Raman_Thermometry
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit as curve_fit

from index_string import index_string
from common_explorer import protect_dashviews, generate_basic_components, add_common_callbacks
from .dataset_cache import dataset_cache

def sibling_path(a, b):
    """
    Returns the path of a filename *b* in the same folder as *a*
    (i.e. dirname(a)/b )
    """
    return os.path.join(os.path.dirname(a), b)


def get_angle(file):
    with h5py.File(file, 'r') as f:
        a = dict(f['/hardware/power_wheel/settings'].attrs.items())['position']
    return(a)
    
# (approximate) relationship between angle and attenuation of beam from thorlabs
def angle_to_OD(angle):
    b = -2
    m = (2-0.04)/270
    return m*angle + b

# manually measure Tmax that day then input that into viewer. Viewer can then return estimate of power from reading angle in h5 file
def angle_to_power(angle, Tmax):
    Tmax = Tmax/(10**-0.04)
    OD = angle_to_OD(angle)
    attenuation = 10**(OD)
    power = Tmax * attenuation
    return power



def add_dash(server, env):
    # ============================== DEFINE DASH ENDPOINT AND PAGE TITLE ==================
    dash_endpoint = "powerfit_viewer"
    dash_app_title = "Power Fitting"
    
    dashapp = dash.Dash(__name__, 
                        server = server, 
                        use_pages = False, 
                        url_base_pathname = f"/datasets/{dash_endpoint}/", 
                        external_stylesheets=[dbc.themes.BOOTSTRAP], 
                        suppress_callback_exceptions = True)

        
    dashapp.index_string = index_string

    basic_layout = generate_basic_components(dash_app_title, reload_interval = 300, one_or_more = "more", kw_suggestion = "picam_readout")

    #  ================================= DEFINE APP COMPONENTS =========================
    additional_app_components = [html.P("You will need to select multiple datasets for the fitting algorithm to function"),
                                 dbc.Row(dcc.Input(id = 'tmax', value=900, placeholder ="enter the max power in mW"), style={'margin-bottom': '10px', 'margin-left':'3px' ,'width':800}),
                                 html.Div(dbc.Button("Update Plot", id = 'plot-button', n_clicks = None), style={'margin-bottom': '30px'}),
                                 html.Hr(id = 'break1'),
                                 html.Hr(id = 'break2'),
                                 dbc.Row([dbc.Col(dcc.Graph(id='fig1', figure = "")),
                                          dbc.Col(html.Div(id = 'file-fit-dropdown-placeholder'))
                                         ]),
                                 dbc.Row([ 
                                    dbc.Col([dcc.Graph(id='fig2', figure = "")], width = {"size":4, "order":1}),
                                   # dbc.Col([dcc.Graph(id='fig3', figure = "")], width = {"size":4, "order":2})
                                     ])
                                 ]


    
    #  ================================= // ================== // =========================
    
    dashapp.layout = dbc.Container(
                                   basic_layout + additional_app_components, 
                                   fluid=True, 
                                   style={"margin": "0 auto", "max-width": "80%"}
                                  )

    #protect_dashviews(dashapp)
    add_common_callbacks(dashapp, env) 
   
    #  ================================= DEFINE APP CALLBACKS =========================
    @dashapp.callback(
        Output(component_id = 'file-fit-dropdown-placeholder', component_property = 'children'),
        Input("kw-checklist", "options"),
        Input("kw-checklist", "value"))
    def offer_fit_choices(file_ops, file_choices):
        print(f"{file_ops=}")
        print(f"{file_choices=}")
        dd_title = html.Div("Select a dataset to plot the spectra and fit for: ", id = 'ddtitle')
        dd_obj = dcc.Dropdown(options = file_ops, value = file_choices[-1], id = 'example-spectra-file')
        return([dd_title, dd_obj])

               
    @dashapp.callback(
        Output(component_id='fig1', component_property='figure'),
        Input(component_id = 'plot-button', component_property = 'n_clicks'),
        Input("kw-checklist", "value"),
        Input("example-spectra-file", "value"),
        Input("tmax", "value"))
    def generate_fig1(nclicks, selected_datasets, fitfile_dsid, tmax):
        if nclicks is None:
            raise PreventUpdate  
        else:
            print(f"{selected_datasets=}")
            dsids = [dsvalue.strip('"').strip("'") for dsvalue in selected_datasets]
            for dsid in dsids:
                print(f"checking for {dsid} in cache")
                dataset_cache(dsid, config=current_app.config, always_sync=False)
                
            files = [glob.glob(f"./assets/{dsid}/*.h5")[-1] for dsid in dsids]
            fitfile = [x for x in files if fitfile_dsid in x][-1]
            
            # =============== USE EQUATION
            angles = [get_angle(f) for f in files]
            print(f"fig 1 - {angles=}")
            power_mw_list = [angle_to_power(a,float(tmax)) for a in angles]
            print(f"fig 1 - {power_mw_list=}")
            
            temp = Raman_Thermometry(filename = fitfile, power_mw = power_mw_list, wa = angles) # in her eg. n = 0
            p1, p1err, p2, p2err, x, y, out = temp.fit_E_A()

            fig = go.Figure(go.Scatter(x=x, y=y, mode = "markers+lines",  marker=dict(size=2), showlegend = False))
            fig.add_trace(go.Scatter(x = x, y = out, mode = "markers+lines",  marker=dict(size=2), showlegend = False))
            fig.update_layout(title=f'Spectra and Fit for {os.path.basename(fitfile)}')
            return(fig)

    
    @dashapp.callback(
        Output(component_id='fig2', component_property='figure'),
        Input(component_id = 'plot-button', component_property = 'n_clicks'),
        Input("kw-checklist", "value"),
        Input("tmax", "value"))
    def generate_fig2_3(nclicks, selected_datasets, tmax):
        if nclicks is None:
            raise PreventUpdate  
        else:
            print("running fig2 callback")
            dsids = [dsvalue.strip('"').strip("'") for dsvalue in selected_datasets]
            for dsid in dsids:
                print(f"checking for {dsid} in cache")
                dataset_cache(dsid, config=current_app.config, always_sync=False)
                
            files = [glob.glob(f"./assets/{dsid}/*.h5")[-1] for dsid in dsids]
            fig = go.Figure()
            fig = make_subplots(rows=1, cols=2, shared_yaxes=False, subplot_titles=("E\' peak", "A\' peak"))
            powers = np.zeros(len(files))
            fitted_p1 = np.zeros([len(files),2])
            fitted_p2 = np.zeros([len(files),2])
            
            # Plot peak location vs. laser power for each file
            angles = [get_angle(f) for f in files]
            print(f"fig 2 - {angles=}")
            power_mw_list = [angle_to_power(a,float(tmax)) for a in angles]
            print(f"fig 2 - {power_mw_list=}")
            for i, fn in enumerate(files):
                temp = Raman_Thermometry(filename = fn, power_mw = power_mw_list, wa = angles)
                p1, p1err, p2, p2err, x, y, out = temp.fit_E_A()

                powers[i] = temp.power
                fitted_p1[i] = p1,p1err
                fitted_p2[i] = p2, p2err
            
            # Fit peak vs. power for each peak
            print(f"{len(powers)=}")
            print(f"{len(fitted_p1[:,0])=}")
            print(f"{len(fitted_p1[:,1])=}")
            popt1, pcov1 = curve_fit(linear, powers, fitted_p1[:,0], sigma=fitted_p1[:,1], absolute_sigma=True)
            popt2, pcov2 = curve_fit(linear, powers, fitted_p2[:,0], sigma=fitted_p2[:,1], absolute_sigma=True)

            fig.add_trace(go.Scatter(x=powers, y=linear(powers, *popt1), mode='lines', line=dict(color='orange'), name=r'$cm^{-1}/mW =$' + str(round(popt1[0],4))), row = 1, col = 1)
            
            fig.add_trace(go.Scatter(x=powers, y=linear(powers, *popt2), mode='lines', line=dict(color='blue'), name=r'$cm^{-1}/mW =$' + str(round(popt2[0],4))), row = 1, col = 2)

            fig.add_trace(go.Scatter(x=powers, y=fitted_p1[:,0], mode='markers', error_y=dict(type='data', array=fitted_p1[:,1], visible=True),
                                         marker=dict(color='orange', symbol='circle'), showlegend = False),  row = 1, col = 1)
            
            fig.add_trace(go.Scatter(x=powers, y=fitted_p2[:,0], mode='markers', error_y=dict(type='data', array=fitted_p2[:,1], visible=True),
                                         marker=dict(color='blue', symbol='circle'), showlegend = False),  row = 1, col = 2)

            fig.update_xaxes(title_text="Laser Power (mW)", row=1, col=2)
            fig.update_yaxes(title_text="Raman Shift ($cm^{-1}$)", row=1, col=2)
            fig.update_layout(xaxis_title='Laser Power (mW)',
                              yaxis_title='Raman Shift ($cm^{-1}$)',
                              width=1000,
                              height=500,
                              margin=dict(l=50, r=50, t=50, b=50))
            
            return(fig)

    #  ================================= // ================== // =========================
    
    return(server)
