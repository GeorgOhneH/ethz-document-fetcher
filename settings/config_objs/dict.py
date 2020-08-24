import logging

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from settings.config_objs.string import ConfigString, WidgetWrapper, AbstractConfigWidget

logger = logging.getLogger(__name__)


class GroupBox(QGroupBox, AbstractConfigWidget):
    data_changed_signal = pyqtSignal()

    def __init__(self, config_obj):
        super().__init__()
        self.setTitle(config_obj.get_gui_name())
        self.config_obj = config_obj
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.init()

    def init(self):
        for name, config_obj in self.config_obj.layout.items():
            config_widget = config_obj.get_widget()
            config_widget.data_changed_signal.connect(self.data_changed_emit)
            self.layout.addWidget(config_widget)

    def clear(self):
        for i in reversed(range(self.layout.count())):
            config_widget = self.layout.itemAt(i).widget()
            config_widget.data_changed_signal.disconnect(self.data_changed_emit)
            config_widget.setParent(None)

    def get_value(self):
        result = {}
        for name, config_obj in self.config_obj.layout.items():
            result[name] = config_obj.get_from_widget()
        return result

    def set_value(self, value):
        if value is None:
            return
        for name, config_obj in self.config_obj.layout.items():
            config_obj.set_to_widget(value.get(name, None))

    def update_widget(self):
        if self.layout.count() > 0:
            self.show()
        else:
            self.hide()

    def data_changed_emit(self):
        self.data_changed_signal.emit()


class DictWidgetWrapper(WidgetWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_label.hide()

    def update_widget(self):
        self.config_widget.update_widget()


class ConfigDict(ConfigString):
    def __init__(self, layout, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._layout = layout

    def init_widget(self):
        return GroupBox(self)

    def get_widget(self) -> WidgetWrapper:
        if self.widget is None:
            self.widget = DictWidgetWrapper(self.init_widget(), hint_text=self.hint_text)
        return self.widget

    @property
    def layout(self):
        return self._layout

    @layout.setter
    def layout(self, layout):
        self._layout = layout
        for name, config_obj in layout.items():
            config_obj.name = name
            config_obj.instance = self.instance
        for name, config_obj in layout.items():
            config_obj.instance_created()
        for name, config_obj in layout.items():
            if config_obj.default is not None:
                config_obj.set(config_obj.default)

    def _get(self):
        result = {}
        for name, config_obj in self._layout.items():
            result[name] = config_obj.get()
        return result

    def _set(self, value):
        for name, config_obj in self._layout.items():
            if name not in value and config_obj.optional:
                continue
            config_obj.set(value[name])

    def _test(self, value, from_widget):
        for name, config_obj in self._layout.items():
            if name not in value:
                if config_obj.optional:
                    continue
                raise ValueError(f"Field '{name}' must exist")

            if not config_obj.is_valid(value[name], from_widget=from_widget):
                raise ValueError(config_obj.msg)

    def update_widget(self):
        for name, config_obj in self._layout.items():
            config_obj.update_widget()
        super().update_widget()

    def update_visibility(self):
        for name, config_obj in self._layout.items():
            config_obj.update_visibility()
        super().update_visibility()

    def set_to_widget(self, value):
        for name, config_obj in self._layout.items():
            config_obj.set_to_widget(value[name])

    def reset_widget(self):
        for name, config_obj in self._layout.items():
            config_obj.reset_widget()
        super().reset_widget()

    def set_parser(self, parser):
        raise NotImplemented

    def _load(self, value):
        raise NotImplemented

    def _save(self):
        raise NotImplemented
