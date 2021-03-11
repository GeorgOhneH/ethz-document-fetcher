from aiohttp import BasicAuth

from settings.config_objs import ConfigList, ConfigDict, ConfigString, ConfigBool

HEADERS_CONFIG = ConfigList(
    gui_name="Headers",
    hint_text="This is only useful if you want to add your own headers",
    optional=True,
    config_obj_default=ConfigDict(
        gui_name="",
        layout={
            "key": ConfigString(
                gui_name="Key",
                optional=True,
            ),
            "value": ConfigString(
                gui_name="Value",
                optional=True,
            ),
        }
    )
)


def headers_config_to_session_kwargs(headers_config) -> dict:
    headers = {d["key"]: d["value"] for d in headers_config}
    return dict(headers=headers)


def _basic_auth_config_use_eth_credentials(instance, from_widget, parent):
    if from_widget:
        use = parent.get_from_widget()["use"]
    else:
        use = parent.get()["use"]
    return use


def _basic_auth_config_custom(instance, from_widget, parent):
    if from_widget:
        use_eth_credentials = parent.get_from_widget()["use_eth_credentials"]
        use = parent.get_from_widget()["use"]
    else:
        use_eth_credentials = parent.get()["use_eth_credentials"]
        use = parent.get()["use"]
    return not use_eth_credentials and use


BASIC_AUTH_CONFIG = ConfigDict(
    optional=True,
    gui_name="Basic Authentication",
    layout={
        "use": ConfigBool(default=False, gui_name="Use Basic Authentication"),
        "use_eth_credentials": ConfigBool(default=False,
                                          gui_name="Use ETH Credentials",
                                          gray_out=True,
                                          active_func=_basic_auth_config_use_eth_credentials),
        "custom": ConfigDict(
            active_func=_basic_auth_config_custom,
            gui_name="Custom",
            gray_out=True,
            layout={
                "username": ConfigString(),
                "password": ConfigString(),
            }
        )
    }
)


def basic_auth_config_to_session_kwargs(basic_auth, download_settings):
    if basic_auth["use"]:
        if basic_auth["use_eth_credentials"]:
            return dict(auth=BasicAuth(login=download_settings.username,
                                       password=download_settings.password))
        else:
            return dict(auth=BasicAuth(login=basic_auth["custom"]["username"],
                                       password=basic_auth["custom"]["password"]))

    return {}
