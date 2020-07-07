from core.template_parser.nodes.base import TemplateNode


class Root(TemplateNode):
    def __init__(self, **kwargs):
        super().__init__(parent=None, **kwargs)

    def _init_parent(self):
        return None

    def _init_position(self):
        return "root"

    def _init_base_path(self, use_folder):
        return ""

    def _init_unique_key(self):
        return "root"
