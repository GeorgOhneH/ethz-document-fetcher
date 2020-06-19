from core.template_parser.nodes.base import TemplateNode


class Folder(TemplateNode):
    def __init__(self, name, parent):
        super().__init__(parent=parent, folder_name=name, unique_key_args=[name])
        self.name = name

    def __str__(self):
        return self.name

    def _init_parent(self):
        return self.parent.add_folder(self)

    def gui_name(self):
        return self.name

    def gui_options(self):
        return [
            ("name", self.name),
        ]
