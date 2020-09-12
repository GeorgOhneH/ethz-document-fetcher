from typing import Dict

from settings.config_objs import ConfigList, ConfigDict, ConfigString, ConfigInt

hello = ConfigList(gui_name="Regrex Patterns",
                   item_name="Pattern",
                   config_obj_default=ConfigDict(layout={
                       "regrex": ConfigString(),
                       "folder": ConfigString()
                   }))


async def producer(session,
                   queue,
                   base_path,
                   site_settings,
                   url,
                   regrex_patterns: hello):
    print(regrex_patterns)


async def get_folder_name(session, **kwargs):
    return "HELLO"
