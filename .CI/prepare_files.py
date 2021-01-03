import boto3
import os
import sys
import shutil
from pprint import pprint
import json


def download_dir(prefix, local, bucket, client):
    """
    params:
    - prefix: pattern to match in s3
    - local: local path to folder in which to place files
    - bucket: s3 bucket with target contents
    - client: initialized s3 client object
    """
    keys = []
    dirs = []
    next_token = ''
    base_kwargs = {
        'Bucket': bucket,
        'Prefix': prefix,
    }
    while next_token is not None:
        kwargs = base_kwargs.copy()
        if next_token != '':
            kwargs.update({'ContinuationToken': next_token})
        results = client.list_objects_v2(**kwargs)
        contents = results.get('Contents')
        for i in contents:
            k = i.get('Key')
            if k[-1] != '/':
                keys.append(k)
            else:
                dirs.append(k)
        next_token = results.get('NextContinuationToken')
    for d in dirs:
        dest_pathname = os.path.join(local, d)
        if not os.path.exists(os.path.dirname(dest_pathname)):
            os.makedirs(os.path.dirname(dest_pathname))
    for k in keys:
        dest_pathname = os.path.join(local, k)
        if not os.path.exists(os.path.dirname(dest_pathname)):
            os.makedirs(os.path.dirname(dest_pathname))
        client.download_file(bucket, k, dest_pathname)


if __name__ == "__main__":
    CI_PATH = os.path.dirname(__file__)
    ROOT_PATH = os.path.dirname(CI_PATH)
    CONFIG_PATH = os.path.join(ROOT_PATH, ".pyupdater", "config.pyu")

    client = boto3.Session(
        aws_access_key_id=os.environ.get("PYU_AWS_ID"),
        aws_secret_access_key=os.environ.get("PYU_AWS_SECRET"),
        region_name="eu-central-1",
    ).client("s3")

    print(os.environ.get("PYU_AWS_ID"))
    print(os.environ.get("PYU_AWS_SECRET"))

    download_dir(sys.platform, CI_PATH, "ethz-document-fetcher-pyupdater", client)

    shutil.move(os.path.join(CI_PATH, "win32", ".pyupdater"), ROOT_PATH)
    shutil.move(os.path.join(CI_PATH, "win32", "pyu-data"), ROOT_PATH)

    if not os.path.exists(os.path.join(ROOT_PATH, ".pyupdater", "config-old.pyu")):

        with open(CONFIG_PATH) as f:
            config_pyu = json.load(f)

        config_pyu["config_dir"] = os.path.join(ROOT_PATH, *config_pyu["config_dir"])
        config_pyu["filename"] = os.path.join(ROOT_PATH, *config_pyu["filename"])
        config_pyu["app_config"]["DATA_DIR"] = os.path.join(ROOT_PATH, *config_pyu["app_config"]["DATA_DIR"])

        with open(CONFIG_PATH, "w+") as f:
            json.dump(config_pyu, f)

    for file_name in os.listdir(CI_PATH):
        if ".spec" in file_name:
            shutil.copy(os.path.join(CI_PATH, file_name), os.path.join(ROOT_PATH, file_name))
