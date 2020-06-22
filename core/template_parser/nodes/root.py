from core.template_parser.nodes.base import TemplateNode


class Root(TemplateNode):
    def __init__(self, site_settings):
        super().__init__(parent=None, site_settings=site_settings)

    def _init_parent(self):
        return None

    def _init_base_path(self, folder_name, use_folder):
        return ""

    def _init_unique_key(self, child_position, **kwargs):
        self.position = "root"
        return "root"
