import copy
import logging

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from settings.config_objs.dict import DictWidgetWrapper
from settings.config_objs.string import ConfigString, AbstractConfigWidget, LineEdit

logger = logging.getLogger(__name__)


class ListLineEdit(LineEdit):
    def get_value(self):
        raw = super(ListLineEdit, self).get_value()
        if raw is None:
            return []
        return [x.strip() for x in raw.split(",") if x.strip()]

    def set_value(self, value):
        if value is None:
            super(ListLineEdit, self).set_value("")
        else:
            super(ListLineEdit, self).set_value(", ".join(value))


class ConfigListString(ConfigString):
    def __init__(self, hint_text="", *args, **kwargs):
        super().__init__(hint_text="Separate by comma. " + hint_text,
                         *args,
                         **kwargs)

    def init_widget(self):
        return ListLineEdit(self)

    def _save(self):
        if not self._value:
            return "[]"
        result = "["
        for x in self._value[:-1]:
            result += str(x) + ", "
        result += self._value[-1] + "]"
        return result

    def _load(self, value):
        if not value:
            return []

        if value[0] != "[" or value[-1] != "]":
            logger.warning(f"Could not load value from {self.name}. Using empty list")
            return []

        return [x.strip() for x in value[1:-1].split(",") if x.strip()]

    def _test(self, value, from_widget):
        if not isinstance(value, list):
            raise ValueError("Value must be a list")

    def set_parser(self, parser):
        parser.add_argument(f"--{self.name.replace('_', '-')}", nargs='*')


class ListWidgetWrapper(QWidget):
    data_changed_signal = pyqtSignal()
    delete = pyqtSignal(object)

    def __init__(self, config_widget, parent=None):
        super().__init__(parent=parent)
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.config_widget = config_widget
        self.config_widget.data_changed_signal.connect(self.data_changed_emit)
        self.layout.addWidget(self.config_widget)

        delete_button = QPushButton("Delete")
        delete_button.setFocusPolicy(Qt.NoFocus)
        delete_button.clicked.connect(self.delete_emit)
        self.layout.addWidget(delete_button)

    def get_value(self):
        return self.config_widget.get_value()

    def set_value(self, value):
        self.config_widget.set_value(value)

    def update_widget(self):
        self.config_widget.config_widget.config_obj.update_widget()

    def data_changed_emit(self, *args, **kwargs):
        self.data_changed_signal.emit()

    def delete_emit(self):
        self.delete.emit(self)


class ListGroupBox(QGroupBox, AbstractConfigWidget):
    data_changed_signal = pyqtSignal()

    def __init__(self, config_obj):
        super().__init__()
        self.config_obj = config_obj
        self.setTitle(config_obj.get_gui_name())
        self.config_objs_layout = QVBoxLayout()
        self.config_objs_layout.setContentsMargins(0, 0, 0, 0)
        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.append_new_widget)
        self.item_container = QWidget(parent=self)
        self.item_container.setLayout(self.config_objs_layout)
        top_layout = QVBoxLayout()
        top_layout.addWidget(self.item_container)
        top_layout.addWidget(self.add_button)
        self.setLayout(top_layout)
        self.init(config_obj.get())

    def init(self, value):
        if value is None:
            return
        for i, sub_value in enumerate(value):
            new_config_obj = self.append_new_widget()
            new_config_obj.set_to_widget(sub_value)
        self.data_changed_emit()

    def clear(self):
        for i in reversed(range(self.config_objs_layout.count())):
            self.remove_item(i)

    def remove_item(self, index):
        config_widget = self.config_objs_layout.itemAt(index).widget()
        self.remove_widget(config_widget)

    def remove_widget(self, widget):
        widget.data_changed_signal.disconnect(self.data_changed_emit)
        widget.delete.disconnect(self.remove_widget)
        widget.setParent(None)
        self.data_changed_emit()

    def append_new_widget(self):
        new_config_obj = copy.deepcopy(self.config_obj.config_obj_default)

        config_widget = ListWidgetWrapper(new_config_obj.get_widget())
        config_widget.data_changed_signal.connect(self.data_changed_emit)
        config_widget.delete.connect(self.remove_widget)
        self.config_objs_layout.addWidget(config_widget)
        self.data_changed_emit()
        return new_config_obj

    def get_value(self):
        result = []
        for i in range(self.config_objs_layout.count()):
            config_widget = self.config_objs_layout.itemAt(i).widget()
            result.append(config_widget.get_value())
        return result

    def set_value(self, value):
        if value is None:
            return
        self.clear()
        self.init(value)

    def update_widget(self):
        if self.config_objs_layout.count() > 0:
            self.item_container.show()
        else:
            self.item_container.hide()

        for i in range(self.config_objs_layout.count()):
            config_widget = self.config_objs_layout.itemAt(i).widget()
            config_widget.update_widget()

    def data_changed_emit(self):
        self.data_changed_signal.emit()


class ConfigList(ConfigString):
    def __init__(self, config_obj_default, *args, **kwargs):
        super().__init__(*args, default=[], **kwargs)
        config_obj_default.parent = self
        if config_obj_default.get_gui_name() is None:
            raise ValueError("config_obj_default must have the gui_name set")
        self.config_obj_default = config_obj_default
        self.config_obj_default.instance = self.instance
        if self.config_obj_default.default is not None:
            self.config_obj_default.set(self.config_obj_default.default)

    def init_widget(self):
        return ListGroupBox(self)

    def _get_new_widget(self):
        return DictWidgetWrapper(self.init_widget(), hint_text=self.hint_text)

    def _test(self, value, from_widget):
        if not isinstance(value, list):
            return False

        for i, sub_value in enumerate(value):
            if not self.config_obj_default.is_valid(sub_value, from_widget=from_widget):
                raise ValueError(self.config_obj_default.msg)

    def set_parser(self, parser):
        raise NotImplemented

    def _load(self, value):
        raise NotImplemented

    def _save(self):
        raise NotImplemented
