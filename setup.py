import getpass
import os

import settings.values as setting_values
from settings import settings

BASE_PATH = os.path.abspath(os.path.dirname(__file__))
BAT_FILE_PATH = os.path.join(BASE_PATH, "run.bat")


def setup():
    print("To skip a value enter nothing")
    for value in settings:
        if not value.is_active():
            continue

        while True:
            user_prompt = value.get_user_prompt()

            if isinstance(value, setting_values.ConfigPassword):
                i = getpass.getpass(user_prompt)
            else:
                print(user_prompt, end="")
                i = input().strip()

            if i == "" and value.is_valid():
                break

            i = value.convert_from_prompt(i)
            if i is None:
                print(value.msg)
                continue

            if not value.test(i):
                print(value.msg)
                continue

            value.set(None, i)
            break

    settings.save()

    with open(BAT_FILE_PATH, "w+") as f:
        f.write(f"python {os.path.join(BASE_PATH, 'main.py')}\n")
        f.write("pause")


if __name__ == "__main__":
    setup()
