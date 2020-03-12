import os
import getpass
from settings import settings
from settings.exceptions import NoValue, InvalidPath

BASE_PATH = os.path.abspath(os.path.dirname(__file__))
BAT_FILE_PATH = os.path.join(BASE_PATH, "run.bat")


def setup():
    settings.init(raise_exception=False)
    data = settings.get_settings()

    print("To skip a value enter nothing")
    for key, value in data.items():
        while True:
            if "password" in key and value:
                value = value[0] + "*" * (len(value)-1)
            current = f" (current: {value})" if value else ""

            if "password" in key:
                i = getpass.getpass(f"Please enter your password{current} (password is not shown): ")
            else:
                current = f" (current: {value})" if value else ""
                print(f"Please enter the value for {key}{current}: ", end="")
                i = input().strip()
            try:
                if not i and value:
                    break
                settings.test_key_value(key, i)
                data[key] = i
                break
            except (NoValue, InvalidPath) as e:
                print("Please enter a valid value")
                continue

    settings.set_settings(data)

    with open(BAT_FILE_PATH, "w+") as f:
        f.write(f"python {os.path.join(BASE_PATH, 'main.py')}\n")
        f.write("pause")


if __name__ == "__main__":
    setup()
