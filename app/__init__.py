import os
import flask
from flask import Flask,session
import datetime
from flask import redirect, url_for
from flask_pyoidc import OIDCAuthentication
from flask_pyoidc.provider_configuration import ProviderConfiguration, ClientMetadata
import dash
from dash import Dash, html, dcc, callback, Output, Input, State, Patch
import argparse
import yaml
import time

def create_app(env_var):
    # config
    env_config_file = f"conf/{env_var}_config.yaml"
    with open(env_config_file, "r") as f:
        env_config = yaml.safe_load(f)

    # secrets
    with open("secrets.yaml", "r") as f:
        secrets = yaml.safe_load(f)

    server = Flask(__name__)
    print(server)
    server.config['environment'] = env_var
    server.config.update(env_config)
    server.config.update(secrets)
    server.config.update({'OIDC_REDIRECT_URI': env_config['redirect_uri'],
                           'SECRET_KEY': secrets['PYOIDC_SECRET'],
                           'PERMANENT_SESSION_LIFETIME': datetime.timedelta(days=1).total_seconds()
                         })
    print("registering the blueprints")
    register_blueprints(server)
    print("blueprint registration complete")
    print("registering the dashapps")
    print(f"server name: {server.config['SERVER_NAME']}")
    register_dashapps(server, env_var)
    return server

   
def register_blueprints(server):
    from app.routes import auth,server_bp
    server.register_blueprint(server_bp)
    print("about to initialize app with auth")
    auth.init_app(server)
    print("app initialization complete")


def register_dashapps(server, env):
    from app.explore_data import add_dash as ad1
    from app.hyperspectra_viewer import add_dash as ad2
    from app.powerfit_viewer import add_dash as ad3
    from app.demo_viewer import add_dash as ad4
    
    server = ad1(server, env) 
    server = ad2(server, env) 
    server = ad3(server, env)
    server = ad4(server, env)

    print("dashapps registered to server")
    return(server)
