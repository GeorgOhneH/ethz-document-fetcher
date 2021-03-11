import os
import sys
import tarfile
import zipfile

if __name__ == "__main__":
    ROOT = os.path.dirname(os.path.dirname(__file__))

    file_name = os.listdir(os.path.join(ROOT, "pyu-data", "new"))[0]

    if sys.platform == "win32":
        platform_dist = "win"
    elif sys.platform == "linux":
        platform_dist = "ubu"
    elif sys.platform == "darwin":
        platform_dist = "mac"
    else:
        raise ValueError("Not supported platform")

    path_to_zip_file = os.path.join(ROOT, "pyu-data", "new", file_name)
    to_path = os.path.join(ROOT, f"dist{platform_dist}")

    if file_name.endswith("tar.gz"):
        with tarfile.open(path_to_zip_file, "r:gz") as tar:
            tar.extractall(to_path)

    elif file_name.endswith("tar"):
        with tarfile.open(path_to_zip_file, "r:") as tar:
            tar.extractall(to_path)

    elif file_name.endswith("zip"):
        with zipfile.ZipFile(path_to_zip_file, 'r') as zip_ref:
            zip_ref.extractall(to_path)
    else:
        raise ValueError(f"Not support file format {file_name}")

    print(f"Moved file from {path_to_zip_file} to {to_path}")
