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
from flask import current_app, session
import sys
import requests
from requests.auth import HTTPBasicAuth 
from app.routes import auth
from general_functions import *
import time

def generate_basic_components(app_name, reload_interval = 45, one_or_more = "more", kw_suggestion = None):
    stime = time.time()
    print(f"starting generate basic components: {stime}")
    basic_components = [dbc.Row(html.Div(dbc.Button("Login", id = 'login-button', n_clicks = None, color = 'primary', size = "sm",
                                               style={'right': '10px','padding': '10px 20px'}),  className="d-grid gap-2 d-md-flex justify-content-md-end", style = {'margin-bottom':'75px'})),
        
                        dbc.Row(html.H1(app_name, id = "page-loaded", style={'textAlign':'center'})),

                        # hiddent things
                        html.Div(None, id = "auth-var"),
                        html.Div(dcc.Location(id = "url", refresh = "False")),
                        html.Div(id = 'hiddendiv'),
                        html.Div(id = "one_or_more_datasets", style={'display': 'none'}, children=one_or_more),
                       
                        # dataset selection
                        html.Div("Select a dataset from the list below or enter a keyword to search for datasets in the box. Then press Go to load data or search results."),
                        dbc.Row([dbc.Col(html.Div(id='authds-dropdown-placeholder'), width = {"size":3, "order":1},  style={ 'margin-bottom': '10px'}),
                                 dbc.Col(dcc.Input(id = 'keyword-search', value = None, placeholder = kw_suggestion), width = {"size":3, "order":2})],  style={ 'margin-bottom': '10px'}),
                        html.Div(dbc.Button("Go", id = 'go-button', n_clicks = None),   style={'width': '100%', 'margin-bottom': '20px'}),
                        html.Div(id = "kw-checklist-placeholder",  style={'margin-bottom': '10px'}),
                        dcc.Interval(
                                id='interval-component',
                                interval=reload_interval*1000, # in milliseconds
                                n_intervals=0
                            ),
                        html.Div(id = 'hiddendiv2'),
                        html.Div(id='hiddendiv3'),]
    etime = time.time()
    print(f"finished generating basic components: {etime}. Total time = {etime - stime}")
    return(basic_components)

    
def protect_dashviews(dashapp):
    PROVIDER_NAME = 'orcid'
    oidc_auth_orcid = auth.oidc_auth(PROVIDER_NAME)
    for view_func in dashapp.server.view_functions:
        if view_func.startswith(dashapp.config.url_base_pathname):
            dashapp.server.view_functions[view_func] = oidc_auth_orcid(dashapp.server.view_functions[view_func]) 


def gen_kw_results(one_or_more, options, values):
    stime = time.time()
    print(f"starting gen_kw_results: {stime}")
    print(f"{one_or_more=}")
    if one_or_more == "one":
        ds_checklist_comp = dcc.RadioItems(options = options, value = values[0], id = 'kw-checklist', style = {"margin-bottom":"10px"})
        text_ = "Select a dataset to explore"
    else:
        print(f"{options=}")
        print(f"{values}")
        ds_checklist_comp = dcc.Checklist(options = options, value = values, id = 'kw-checklist', style = {"margin-bottom":"10px", "padding": "20px"})
        text_ = "Select one or more dataset(s) to explore"
    etime = time.time()
    print(f"finsihed gen_kw_results:{etime}. Total time = {etime - stime}")
    return([html.H5(text_,  style={'margin-bottom': '10px'}), ds_checklist_comp])


def filter_on_viewer_compatibility(list_to_filter):
    stime = time.time()
    print(f"start filter on viewer: {stime}")
    dropdown_options = [{"label":x[0],"value":x[1]} for x in list_to_filter]
    etime = time.time()
    print(f"finished filter on viewer: {etime}. Total time = {etime - stime}")
    return(dropdown_options)


def get_session_orcid(session):
    stime = time.time()
    print(f"start get session orcid {stime}")
    try:
        orcid = session['user_info']['sub']
    except:
        orcid = "0000-0000-0000-0000"
    etime = time.time()
    print(f"finished get session orcid: {etime}. Total time = {etime - stime}")
    return(orcid)


def get_authorized_datasets(orcid, current_app, url_parse, kw = None):
    stime = time.time()
    print(f"start get auth datasets {stime}")
    from viewer_config import viewer_data_format_map as viewer_map
    
    if kw is None:
        api_req = f"https://crucible.lbl.gov/api/users/{orcid}/readable_datasets"
    else:
        api_req = f"https://crucible.lbl.gov/api/users/{orcid}/readable_datasets_by_keyword/{kw}"
    try:
        print("trying auth")
        if len(url_parse) > 0:
            viewer_type = url_parse[0]
            viewer_options = viewer_map[viewer_type]
            for k,v in viewer_options.items():
                api_req += (f"?{k}={v}")
        print(f"{api_req=}")
        authorized_datasets = requests.request(method="get", url=api_req, 
                                               auth = HTTPBasicAuth("readonly", current_app.config['crucible_db_web_password']))
        authorized_datasets = authorized_datasets.json()
        print(f"{authorized_datasets=}")
    except Exception as err:
        print(err)
        authorized_datasets = []

    etime = time.time()
    print(f"finished get auth datasets: {etime}. Total time = {etime - stime}")
    return(authorized_datasets)



def authorize_web_user(n, one_or_more, url_path):
    
    url_parse = [x for x in url_path.split("/datasets/")[1].split("/") if x != ""]
    orcid = get_session_orcid(session)
    authorized_datasets = get_authorized_datasets(orcid, current_app, url_parse)    

    # these are the datasets the user has permission to see
    dropdown_options = filter_on_viewer_compatibility(authorized_datasets)
    ds_dropdown_comp = dcc.Dropdown(options = dropdown_options, value = None, id = "dataset-options")
    
    # initialize as none
    auth_stat = None
    kwcomps = None
    redirect_loc = None
    
    # if dataset info passed to browser, check auth
    if len(url_parse) <= 1:
        auth_stat = "Authorized"
        
    elif "dsid" in url_parse[-1]:
        dsid = url_parse[-1].replace("dsid=", "")
        dsnames = [x[0] for x in authorized_datasets if x[1] == dsid]
        if len(dsnames) > 0:
            kwcomps = gen_kw_results(one_or_more, [{"label":dsnames,"value":dsid}], [dsid])
            auth_stat = "Authorized"

    elif "kw" in url_parse[-1]:
        kw = url_parse[-1].replace("kw=", "")
        try:
            kw_matches = get_authorized_datasets(orcid, current_app, url_parse, kw)
            kw_options = filter_on_viewer_compatibility(kw_matches)
            kwcomps = gen_kw_results(one_or_more, kw_options, [kw_matches[-1][1]])
            auth_stat = "Authorized"
        except Exception as err:
            print(err)

    else:
        ds_dropdown_comp = None
        browser = url_path.split("/")[-2]
        redirect_loc = dcc.Location(pathname = f"/datasets/{browser}/", id = 'datasetpage', refresh = True)
    
    return(auth_stat, ds_dropdown_comp, kwcomps, redirect_loc)


def list_local_datasets(url_parse, kw = None):
    from viewer_config import viewer_data_format_map as viewer_map
    if len(url_parse) > 0:
        viewer_type = url_parse[0]
        viewer_options = viewer_map[viewer_type]
    search_keys = ['dataset_name', 'unique_id', 'keywords'] + list(viewer_options.keys())

    # get the info you need for each dataset
    found_ds = glob.glob("./assets/*/*.json")
    ds_info_list = []
    for d in found_ds:
        print(d)
        d_sub = {}
        with open(d) as f:
            details = json.load(f)
        for k in search_keys:
            d_sub[k] = details[k] 
        ds_info_list += [d_sub]

    # filter on measurement, data format, and/or keywords
    for k in list(viewer_options.keys()):
        ds_info_list = [x for x in ds_info_list if x[k] == viewer_options[k]]

    if kw is not None:
        ds_info_list = [x for x in ds_info_list if any([kw in w for w in x['keywords']])]
        
    # return as list formatted the same as get_authorized_datasets
    return_ds = [[x['dataset_name'], x['unique_id']] for x in ds_info_list]
    return(return_ds)

                        
def authorize_local_user(n, one_or_more, url_path):
    
    url_parse = [x for x in url_path.split("/datasets/")[1].split("/") if x != ""]
    authorized_datasets = list_local_datasets(url_parse)
    dropdown_options = filter_on_viewer_compatibility(authorized_datasets)
    ds_dropdown_comp = dcc.Dropdown(options = dropdown_options, value = None, id = "dataset-options")
    
    # initialize as none
    auth_stat = None
    kwcomps = None
    redirect_loc = None
    
    # if dataset info passed to browser, check auth
    if len(url_parse) <= 1:
        auth_stat = "Authorized"
        
    elif "dsid" in url_parse[-1]:
        dsid = url_parse[-1].replace("dsid=", "")
        dsnames = [x[0] for x in authorized_datasets if x[1] == dsid]
        if len(dsnames) > 0:
            kwcomps = gen_kw_results(one_or_more, [{"label":dsnames,"value":dsid}], [dsid])
            auth_stat = "Authorized"

    elif "kw" in url_parse[-1]:
        kw = url_parse[-1].replace("kw=", "")
        try:
            kw_matches = list_local_datasets(url_parse, kw)
            kw_options = filter_on_viewer_compatibility(kw_matches)
            kwcomps = gen_kw_results(one_or_more, kw_options, [kw_matches[-1][1]])
            auth_stat = "Authorized"
        except Exception as err:
            print(err)

    else:
        ds_dropdown_comp = None
        browser = url_path.split("/")[-2]
        redirect_loc = dcc.Location(pathname = f"/datasets/{browser}/", id = 'datasetpage', refresh = True)
    
    return(auth_stat, ds_dropdown_comp, kwcomps, redirect_loc)













# ================================================================================================= CALLBACKS 
def add_common_callbacks(app, env):
    if env != "local":
        @app.callback(
            Output(component_id='auth-var', component_property='value'),
            Output(component_id = 'authds-dropdown-placeholder', component_property = 'children'),
            Output(component_id = 'kw-checklist-placeholder', component_property = 'children'),
            Output(component_id = 'hiddendiv', component_property = 'children'),
            Input("page-loaded", "value"),
            Input('interval-component','n_intervals'),
            Input('one_or_more_datasets', 'children'),
            Input("url", "pathname"))
        def authorize_user(pageload, n, one_or_more, url_path):
            return authorize_web_user(n, one_or_more, url_path)

    else:
        @app.callback(
            Output(component_id='auth-var', component_property='value'),
            Output(component_id = 'authds-dropdown-placeholder', component_property = 'children'),
            Output(component_id = 'kw-checklist-placeholder', component_property = 'children'),
            Output(component_id = 'hiddendiv', component_property = 'children'),
            Input("page-loaded", "value"),
            Input('interval-component','n_intervals'),
            Input('one_or_more_datasets', 'children'),
            Input("url", "pathname"))
        def authorize_user(pageload, n, one_or_more, url_path):
            return authorize_local_user(n, one_or_more, url_path)


    @app.callback(
            Output(component_id = 'hiddendiv2', component_property='children'),
            Input(component_id = 'dataset-options', component_property = 'value'),
            Input(component_id = 'keyword-search', component_property='value'),
            Input(component_id = 'go-button', component_property = 'n_clicks'),
            Input(component_id ='url', component_property = 'pathname'))
    def setup_explorer(dataset, keyword,go, url):
        if go is None:
            raise PreventUpdate  
        else:
            stime = time.time()
            print(f"starting setup explorer callback {stime}")
            print(url.split("/datasets/")[1].split("/"))
            browser = url.split("/datasets/")[1].split("/")[0]
            if dataset is not None:
                etime = time.time()
                print(f"finished setup explorer: {etime}. Total time = {etime - stime}")
                return(dcc.Location(pathname = f"/datasets/{browser}/dsid={dataset}", id = 'datasetpage', refresh = True))
            elif keyword is not None:
                etime = time.time()
                print(f"finished setup explorer: {etime}. Total time = {etime - stime}")
                return(dcc.Location(pathname = f"/datasets/{browser}/kw={keyword}", id = 'datasetpage', refresh = True))
            else:
                etime = time.time()
                print(f"finished setup explorer: {etime}. Total time = {etime - stime}")
                return(dcc.Location(pathname = f"/datasets/{browser}/", id = 'datasetpage', refresh = True))


    @app.callback(
        Output(component_id='hiddendiv3', component_property='children'),
        Input(component_id = 'login-button', component_property = 'n_clicks'))
    def return_browser(n_clicks):
        if n_clicks is None:
            raise PreventUpdate
        else:
            return(dcc.Location(pathname = f"/dash/", id = 'loginpage', refresh = True))

