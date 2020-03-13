import os
import getpass
from settings import settings
from settings.exceptions import InvalidPath

BASE_PATH = os.path.abspath(os.path.dirname(__file__))
BAT_FILE_PATH = os.path.join(BASE_PATH, "run.bat")


def setup():
    settings.init(raise_exception=False)
    data = settings.get_settings()

    print("To skip a value enter nothing")
    for key, value in data.items():
        while True:

            try:
                if "password" in key:
                    censored = value[0] + "*" * (len(value)-1)
                    current = f" (current: {censored})" if value else ""
                    i = getpass.getpass(f"Please enter your password{current} (password is not shown): ")
                elif "use_" in key:
                    current = f" (current: yes)" if value else " (current: no)"
                    current += " (yes/no)"
                    print(f"Please enter the value for {key}{current}: ", end="")
                    i = input().strip()
                    if not i:
                        break
                    i = True if "y" in i.lower() else False
                else:
                    current = f" (current: {value})" if value else ""
                    print(f"Please enter the value for {key}{current}: ", end="")
                    i = input().strip()
                if i == "":
                    break
                settings.test_key_value(key, i)
                data[key] = i
                break
            except InvalidPath as e:
                print("Please enter a valid value")
                continue

    settings.set_settings(data)

    with open(BAT_FILE_PATH, "w+") as f:
        f.write(f"python {os.path.join(BASE_PATH, 'main.py')}\n")
        f.write("pause")


if __name__ == "__main__":
    setup()
