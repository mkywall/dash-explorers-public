import datetime
import os
import flask
from flask import Flask,Blueprint,jsonify, redirect, url_for,request,g,current_app,session
from datetime import datetime
from flask_pyoidc.user_session import UserSession
from flask_pyoidc import OIDCAuthentication
from flask_pyoidc.provider_configuration import ProviderConfiguration, ClientMetadata
from general_functions import *


with open("secrets.yaml", "r") as f:
    secrets = yaml.safe_load(f)
f.close()
client_secret = secrets['ORCID_CLIENT_SECRET']
secret_key = secrets['PYOIDC_SECRET']


PROVIDER_NAME = 'orcid'
CLIENT_META = ClientMetadata(client_id='APP-AXDIPEVR6IMA0RL7', client_secret=client_secret)
PROVIDER_CONFIG = ProviderConfiguration(issuer='https://orcid.org/', client_metadata=CLIENT_META)

auth = OIDCAuthentication({PROVIDER_NAME: PROVIDER_CONFIG})

server_bp = Blueprint('main', __name__ )

# could replace with API call too..
def get_proposals_using_orcid(orcid_id):
    if apikey is None:
        secrets = load_config(f".secrets_development")
        apikey = secrets['PROPDB_APIKEY']
    response = requests.request(method="get", url=f"https://foundry-admin.lbl.gov/api/json/sciCat-GetUser.aspx?key={apikey}&orcid={orcid_id}")
    if response.text != '' and response.status_code == 200:
        return(response.json())
    else:
        print(f"user with orcid ID {orcid_id} not found in user database")
        return(None)


@server_bp.route('/dash/')
@auth.oidc_auth(PROVIDER_NAME)
def login():
    print("routed to /dash ... running the login function")
    user_session = UserSession(session)
    session['user_info'] = user_session.userinfo
    session.modified = True
    session.modified = True
    print(f"you should now be redirected to the dash endpoint /datasets")
    return redirect('/datasets')
