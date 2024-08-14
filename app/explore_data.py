from datetime import datetime 
import dash
import flask
from dash import Dash, html, dcc, callback, Output, Input, State, Patch
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from flask import current_app,session
from flask_pyoidc import OIDCAuthentication
from flask_pyoidc.provider_configuration import ProviderConfiguration, ClientMetadata
from index_string import *
import time

def add_dash(server, env):
    from app.routes import auth
    PROVIDER_NAME = 'orcid'
    oidc_auth_orcid = auth.oidc_auth(PROVIDER_NAME)
    browsers = ['hyperspectra_viewer', 'powerfit_viewer', 'dvs_viewer']

    def protect_dashviews(dashapp):
        for view_func in dashapp.server.view_functions:
            if view_func.startswith(dashapp.config.url_base_pathname):
                dashapp.server.view_functions[view_func] = oidc_auth_orcid(dashapp.server.view_functions[view_func])

    dashapp = dash.Dash(__name__,
                        server=server,
                        use_pages = False,
                        url_base_pathname = "/datasets/",
                        external_stylesheets=[dbc.themes.BOOTSTRAP],
                        suppress_callback_exceptions = True)
    

    dashapp.index_string = index_string
    
    dashapp.layout = dbc.Container([
                            dbc.Row(html.Div(dbc.Button("Login", id = 'login-button', n_clicks = None, color = 'primary', size = "sm",
                                               style={'right': '10px','padding': '10px 20px'}),  className="d-grid gap-2 d-md-flex justify-content-md-end", style = {'margin-bottom':'75px'})),
        
                            dbc.Row(html.Div(dcc.Location(id='url', refresh=False))),
                            html.H5("Select the type of data browser you would like to explore or login to see all of your datasets.", id = 'page-loaded', style = {'margin-bottom':'10px'}),
                            dcc.Dropdown(browsers, value = None, id = 'chosen_browser',style ={'margin-bottom':'20px'}),
                            dbc.Button("Browse", id = 'go-button', n_clicks = None),
                            html.Div(id='hiddendiv'),
                            html.Div(id='hiddendiv3')
        ],  
        fluid=True, 
        style={"margin": "0 auto", "max-width": "70%"})

    #protect_dashviews(dashapp)


    
    # ====================================== CALLBACKS
    '''
    RETURN BROWSER PAGE
    '''

    @dashapp.callback(
        Output(component_id='hiddendiv', component_property='children'),
        Input(component_id = 'chosen_browser', component_property = 'value'), 
        Input(component_id = 'go-button', component_property = 'n_clicks'))
    def return_browser(chosen_browser, n_clicks):
        if n_clicks is None:
            raise PreventUpdate
        else:
            print(f"sending to browser: {time.time()}")
            return(dcc.Location(pathname = f"/datasets/{chosen_browser}", id = 'browserpage', refresh = True))
            
    @dashapp.callback(
        Output(component_id='hiddendiv3', component_property='children'),
        Input(component_id = 'login-button', component_property = 'n_clicks'))
    def return_browser(n_clicks):
        if n_clicks is None:
            raise PreventUpdate
        else:
            return(dcc.Location(pathname = f"/dash/", id = 'loginpage', refresh = True))


    return(server)