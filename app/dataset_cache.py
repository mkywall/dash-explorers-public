import yaml
import subprocess as sp
import json
import os

def run_shell(cmd):
    return(sp.run(cmd, stdout = sp.PIPE, stderr = sp.STDOUT, shell = True, universal_newlines = True, check = True))


def dataset_cache(dsid, config, always_sync=False):
    """
    Check if a dataset is cached in ./assets
    if not copy from GCP bucket using rclone
    """
    #f"rclone sync mf-cloud-storage:mf-storage-prod/{dsid} ./assets/{dsid}"

    if not always_sync:
        if os.path.exists(f"./assets/{dsid}/{dsid}.json"):
            return

    print(f"dataset_cache {repr(dsid)=} ")
    creds = json.dumps(config['gcs_service_account_credentials']).replace('"', '\\"')


    cmd_args = ["rclone sync -v", 
        f"--gcs-client-id={config['gcs_client_id']}" ,
        f"--gcs-client-secret={config['gcs_client_secret']}",
        f"--gcs-project-number={config['gcs_project_number']}",
        f'--gcs-service-account-credentials="{creds}"',
    #    --gcs-service-account-file=~/.config/mf-crucible-d0f164576449.json \  ## now using json file inline
        "--gcs-object-acl=projectPrivate",
        "--gcs-bucket-acl=projectPrivate",
        "--gcs-env-auth=true" ,
        f":gcs:mf-storage-prod/{dsid} ./assets/{dsid}"
    ]

    resp = run_shell("   ".join(cmd_args))

if __name__ == '__main__':
    env_config_file = f"conf/local_config.yaml"
    with open(env_config_file, "r") as f:
        config = yaml.safe_load(f)    
    with open(".secrets", "r") as f:
        secrets = yaml.safe_load(f)

    dsid = "0sey9bqjn9zm3000w9yab5t2dm"

    dataset_cache(dsid, config,secrets)