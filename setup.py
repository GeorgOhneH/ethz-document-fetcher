import getpass
import os

import settings.values as setting_values
from settings import settings
from settings.exceptions import InvalidPath

BASE_PATH = os.path.abspath(os.path.dirname(__file__))
BAT_FILE_PATH = os.path.join(BASE_PATH, "run.bat")


def setup():
    print("To skip a value enter nothing")
    for value in settings.values:
        if not value.is_active():
            break
        while True:
            try:
                if isinstance(value, setting_values.Password):
                    if value.get_value():
                        censored = value.get_value()[0] + "*" * (len(value.get_value())-1)
                        current = f" (current: {censored})"
                    else:
                        current = ""
                elif isinstance(value, setting_values.Bool):
                    current = f" (current: yes)" if value.get_value() else " (current: no)"
                    current += " (yes/no)"
                    print(f"Please enter the value for {value.name}{current}: ", end="")
                else:
                    current = f" (current: {value.get_value()})" if value.get_value() else ""
                    print(f"Please enter the value for {value.name}{current}: ", end="")

                if isinstance(value, setting_values.Password):
                    i = getpass.getpass(f"Please enter your password{current} (password is not shown): ")
                else:
                    i = input().strip()

                if i == "":
                    break

                if isinstance(value, setting_values.Bool):
                    value._value = i
                else:
                    value.set_value(None, i)
                break

            except InvalidPath as e:
                print(str(e))
                continue

    settings.save()

    with open(BAT_FILE_PATH, "w+") as f:
        f.write(f"python {os.path.join(BASE_PATH, 'main.py')}\n")
        f.write("pause")


if __name__ == "__main__":
    setup()
