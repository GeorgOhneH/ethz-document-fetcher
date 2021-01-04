import os
import sys
import boto3
import botocore


def upload_directory(bucket, destination, local_directory, client):
    for root, dirs, files in os.walk(local_directory):

        for filename in files:
            local_path = os.path.join(root, filename)

            # construct the full Dropbox path
            relative_path = os.path.relpath(local_path, local_directory)
            s3_path = os.path.join(destination, relative_path).replace("\\", "/")

            try:
                client.head_object(Bucket=bucket, Key=s3_path)
                client.delete_object(Bucket=bucket, Key=s3_path)
                print(f"Deleted {s3_path}")
            except botocore.exceptions.ClientError as e:
                pass
            client.upload_file(local_path, bucket, s3_path)
            print(f"Uploaded {local_path}")


if __name__ == "__main__":

    local_directory_updater = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".pyupdater")
    local_directory_data = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pyu-data")

    bucket = "ethz-document-fetcher-pyupdater"

    client = boto3.Session(
        aws_access_key_id=os.environ.get("PYU_AWS_ID"),
        aws_secret_access_key=os.environ.get("PYU_AWS_SECRET"),
        region_name="eu-central-1",
    ).client("s3")

    upload_directory(bucket, os.path.join(sys.platform, "pyu-data"), local_directory_data, client)

    s3_path = f"{sys.platform}/.pyupdater/config.pyu"
    s3_path_old = f"{sys.platform}/.pyupdater/config-old.pyu"

    client.copy_object(Bucket=bucket, CopySource=f"{bucket}/{s3_path}", Key=s3_path_old)
    client.delete_object(Bucket=bucket, Key=s3_path)
    print(f"Copied {s3_path} to {s3_path_old}")

    client.upload_file(os.path.join(local_directory_updater, "config.pyu"), bucket, s3_path)
    print(f"Uploaded {local_directory_updater}")
