from .values import *


def get_key_value(f):
    for line in f.readlines():
        if SEPARATOR in line:
            key, value = [x.strip() for x in line.split(SEPARATOR)]
            yield key, value


class Settings(object):
    def __init__(self):
        video_portal = Bool(name="use_video_portal", value="yes")
        base_path = Path(name="base_path")
        self.values = [
            String(name="username"),
            Password(name="password"),
            base_path,
            video_portal,
            Path(name="video_portal_path", active_func=video_portal.get_value),
            String(name="portal_nus2_2020_password", active_func=video_portal.get_value),
            String(name="portal_nus2_2019_password", active_func=video_portal.get_value),
            String(name="portal_inf1_2020_password", active_func=video_portal.get_value),
            String(name="portal_inf1_2019_password", active_func=video_portal.get_value),
        ]
        self.init()

    def init(self):
        current_settings = {}
        if os.path.exists(SETTINGS_PATH):
            with open(SETTINGS_PATH, "r") as f:
                for key, file_value in get_key_value(f):
                    current_settings[key] = file_value

        for value in self.values:
            file_value = current_settings.get(value.name, None)
            if file_value is not None:
                value.load_value(file_value)
            setattr(Settings, value.name, property(value.get_value, value.set_value))

    def check_if_set(self):
        for value in self.values:
            if value.is_active() and not value.is_set():
                return False
        return True

    def save(self):
        with open(SETTINGS_PATH, "w+") as f:
            for value in self.values:
                f.write(f"{value.name}{SEPARATOR}{value._value}\n")
