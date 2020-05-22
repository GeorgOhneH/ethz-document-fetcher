from .values import *


def get_key_value(f):
    for line in f.readlines():
        if SEPARATOR in line:
            key, value = [x.strip() for x in line.split(SEPARATOR)]
            yield key, value


class SettingBase(type):
    def __new__(mcs, name, bases, attrs, **kwargs):
        values = []
        for key, value in attrs.items():
            if isinstance(value, ConfigString):
                value.name = key
                attrs[key] = property(value.get, value.set)
                values.append(value)
        attrs["_values"] = values
        return super().__new__(mcs, name, bases, attrs)


class Settings(metaclass=SettingBase):
    def __init__(self):
        current_settings = {}
        if os.path.exists(SETTINGS_PATH):
            with open(SETTINGS_PATH, "r") as f:
                for key, file_value in get_key_value(f):
                    current_settings[key] = file_value

        for value in self._values:
            file_value = current_settings.get(value.name, None)
            if file_value is not None:
                value.load(file_value)

    def __iter__(self):
        return iter(self._values)

    def check_if_valid(self):
        for value in self._values:
            if not value.is_valid():
                return False
        return True

    def save(self):
        with open(SETTINGS_PATH, "w+") as f:
            for value in self._values:
                string = value.save()
                if string is not None:
                    f.write(f"{value.name}{SEPARATOR}{value.save()}\n")


class AppSettings(Settings):
    username = ConfigString(optional=True)
    password = ConfigPassword(optional=True)
    base_path = ConfigPath(default=os.getcwd())
    template_path = ConfigPath(absolute=False, default=os.path.join("templates", "FS2020", "itet", "semester2.yml"))
    loglevel = ConfigOption(default="INFO", options=["ERROR", "WARNING", "INFO", "DEBUG"])
    allowed_extensions = ConfigList(optional=True)
    forbidden_extensions = ConfigList(optional=True, default=["video"])
    keep_replaced_files = ConfigBool(default=False)
    force_download = ConfigBool(default=False, active_func=lambda: False)
