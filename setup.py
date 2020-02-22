import os
import shutil


def setup():
    base_path = os.path.dirname(__file__)
    settings_path = os.path.join(base_path, "settings.config")
    template_path = os.path.join(base_path, "settings\\settings.config.template")

    settings = {}

    with open(template_path, "r") as f:
        for line in f.readlines():
            if "=" in line:
                key, value = [x.strip() for x in line.split("=")]
                settings[key] = value

    with open(settings_path, "r") as f:
        for line in f.readlines():
            if "=" in line:
                key, value = [x.strip() for x in line.split("=")]
                settings[key] = value

    with open(settings_path, "w+") as f:
        for key, value in settings.items():
            f.write(f"{key}={value}\n")


if __name__ == "__main__":
    setup()
