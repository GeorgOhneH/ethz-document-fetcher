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
            if isinstance(value, String):
                value.name = key
                attrs[key] = property(value.get_value, value.set_value)
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
                value.load_value(file_value)

    def __iter__(self):
        return iter(self._values)

    def check_if_set(self):
        for value in self._values:
            if value.is_active() and not value.is_set():
                return False
        return True

    def save(self):
        with open(SETTINGS_PATH, "w+") as f:
            for value in self._values:
                f.write(f"{value.name}{SEPARATOR}{value._value}\n")


class AppSettings(Settings):
    username = String()
    password = Password()
    base_path = Path()
    model_path = Path(absolute=False, default=os.path.join("models", "FS2020", "itet.yml"))
    download_videos = Bool(default=True)
    loglevel = Option(default="INFO", options=["ERROR", "WARNING", "INFO", "DEBUG"])
