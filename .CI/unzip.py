import zipfile
import os
import sys


def list_files(startpath):
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * (level)
        print('{}{}/'.format(indent, os.path.basename(root)))
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            print('{}{}'.format(subindent, f))


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
    to_path = os.path.join(ROOT, f"dist{platform_dist}")
    with zipfile.ZipFile(path_to_zip_file, 'r') as zip_ref:
        zip_ref.extractall(to_path)

    list_files(to_path)

    print(f"Moved file from {path_to_zip_file} to {to_path}")
