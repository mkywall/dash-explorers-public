from app import create_app
import argparse
import yaml
import os
import subprocess as sp

def run_shell(cmd):
    return(sp.run(cmd, stdout = sp.PIPE, stderr = sp.STDOUT, shell = True, universal_newlines = True, check = True))
    
parser = argparse.ArgumentParser(description='Grab any command line arguments passed in through the docker run command')
parser.add_argument('app')
parser.add_argument('environment')
args = parser.parse_args()

print(args.environment)

app = create_app(args.environment)

if __name__ == '__main__':
     print(f'Available at {app.config["redirect_uri"].replace("/auth", "")}')
     app.run(port=app.config['port'], host='0.0.0.0', ssl_context = "adhoc")
