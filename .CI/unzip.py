import zipfile
import os
import sys

if __name__ == "__main__":
    ROOT = os.path.dirname(os.path.dirname(__file__))

    with open(os.path.join(ROOT, "version.txt")) as f:
        PYU_VERSION = f.read().strip()[1:]

    if sys.platform == "win32":
        platform = "win"
        platform_dist = "win"
    elif sys.platform == "linux":
        platform = "linux"
        platform_dist = "ubu"
    elif sys.platform == "darwin":
        platform = "mac"
        platform_dist = "mac"
    else:
        raise ValueError("Not supported platform")

    path_to_zip_file = os.path.join(ROOT, "pyu-data", "new", f"ethz-document-fetcher-{platform}-{PYU_VERSION}.zip")
    with zipfile.ZipFile(path_to_zip_file, 'r') as zip_ref:
        zip_ref.extractall(os.path.join(ROOT, f"dist{platform_dist}"))