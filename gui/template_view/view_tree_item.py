import logging
import os
import time

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from core.storage import cache
from gui.application import Application
from gui.constants import ASSETS_PATH
from gui.dynamic_widgets import DynamicIconLabel

logger = logging.getLogger(__name__)


class MovieLabel(QLabel):
    def __init__(self, path, width, height, parent=None):
        super().__init__(parent=parent)

        self.movie = QMovie(path, QByteArray(), self)
        self.movie.setScaledSize(QSize(width, height))

        self.setFixedSize(width, height)

        self.movie.setCacheMode(QMovie.CacheAll)
        self.movie.setSpeed(200)
        self.setMovie(self.movie)
        self.movie.start()


class TreeWidgetItem(QTreeWidgetItem):
    STATE_NOTHING = 0
    STATE_IDLE = 1
    STATE_LOADING = 2
    STATE_ERROR = 3
    STATE_WARNING = 4
    STATE_SUCCESS = 5

    COLUMN_NAME = 0
    COLUMN_ADDED_FILE = 1
    COLUMN_REPLACED_FILE = 2
    COLUMN_STATE = 3
    COLUMN_TYPE = 4

    def __init__(self, template_node):
        super().__init__()
        self.template_node = template_node
        self.name_widget = None

        self.added_new_file_count = 0
        self.replaced_file_count = 0

        self.error_msgs = []
        self.warning_msgs = []

        self.active_item_count = 0
        self.state = self.STATE_NOTHING
        self.children = []
        self.custom_parent = None

        app = Application.instance()

        app.settings_saved.connect(self.emit_data_changed)

    def init_widgets(self):
        self.name_widget = TreeWidgetItemName(name=self.template_node.get_gui_name(),
                                              icon_path=self.template_node.get_gui_icon_path(),
                                              check_state=self.template_node.meta_data.get("check_state", Qt.Checked))
        self.treeWidget().setItemWidget(self, self.COLUMN_NAME, self.name_widget)

        self.name_widget.state_check_changed.connect(self.update_checked)
        self.name_widget.state_check_changed.connect(self.emit_data_changed)

        self.setText(self.COLUMN_TYPE, str(self.template_node.get_type_name()))
        self.setExpanded(True)
        if not self.template_node.is_producer:
            return
        self._set_state(self.STATE_IDLE)
        self.setText(self.COLUMN_ADDED_FILE, str(self.added_new_file_count))
        self.setTextAlignment(self.COLUMN_ADDED_FILE, Qt.AlignRight | Qt.AlignVCenter)
        self.setText(self.COLUMN_REPLACED_FILE, str(self.replaced_file_count))
        self.setTextAlignment(self.COLUMN_REPLACED_FILE, Qt.AlignRight | Qt.AlignVCenter)

    def load_from_cache(self, name):
        download_settings = Application.instance().download_settings
        if download_settings.save_path is None:
            return []
        path_name = download_settings.save_path.replace("\\", "").replace("/", "").replace(":", "").replace(
            ".", "")
        json = cache.get_json(name + path_name)
        if self.template_node.unique_key not in json:
            result = []
            json[self.template_node.unique_key] = result
            return result

        return json[self.template_node.unique_key]

    def emit_data_changed(self):
        self.treeWidget().emit_item_changed(self, 0)

    @staticmethod
    def state_to_string(state):
        if state == TreeWidgetItem.STATE_IDLE:
            return "Idle"
        elif state == TreeWidgetItem.STATE_LOADING:
            return "Loading"
        elif state == TreeWidgetItem.STATE_SUCCESS:
            return "Finished"
        elif state == TreeWidgetItem.STATE_ERROR:
            return "Error"
        elif state == TreeWidgetItem.STATE_WARNING:
            return "Warning"
        elif state == TreeWidgetItem.STATE_NOTHING:
            return ""
        else:
            raise ValueError("Not valid state")

    def state_text(self):
        return self.state_to_string(self.state)

    def reset(self):
        if self.state == self.STATE_NOTHING:
            return
        self.set_idle()

    def _set_state(self, state, msg=None):
        if not self.template_node.is_producer:
            return
        self.state = state
        self.setText(self.COLUMN_STATE, self.state_to_string(state))
        self.name_widget.set_state(state, msg)
        self.emit_data_changed()

    def set_idle(self):
        self.active_item_count = 0
        self.error_msgs.clear()
        self.warning_msgs.clear()
        self._set_state(self.STATE_IDLE)

    def set_loading(self, msg=None):
        self.active_item_count += 1
        self._set_state(self.STATE_LOADING, msg)

    def set_error(self, msg=None):
        self._set_state(self.STATE_ERROR, msg)

    def got_error(self, msg=None):
        if msg is not None:
            self.error_msgs.append(msg)

    def set_warning(self, msg=None):
        self._set_state(self.STATE_WARNING, msg)

    def got_warning(self, msg=None):
        if msg is not None and self.state != self.STATE_SUCCESS:
            self.warning_msgs.append(msg)

    def set_success(self, msg=None):
        self.active_item_count -= 1
        if self.active_item_count < 0:
            logger.warning("Active count is negative")
        if self.active_item_count == 0:
            if self.error_msgs:
                self.set_error("\n".join(self.error_msgs[:min(5, len(self.error_msgs))]))
                return
            if self.warning_msgs:
                self.set_warning("\n".join(self.warning_msgs[:min(5, len(self.warning_msgs))]))
                return
            self._set_state(self.STATE_SUCCESS, msg)

    def set_folder_name(self, folder_name):
        self.template_node.folder_name = folder_name
        self.name_widget.set_name(folder_name)
        self.emit_data_changed()

    def set_base_path(self, base_path):
        self.template_node.base_path = base_path
        self.emit_data_changed()

    def added_new_file(self, path):
        self.added_new_file_count += 1
        self.setText(self.COLUMN_ADDED_FILE, str(self.added_new_file_count))
        added_files = self.load_from_cache("added_files")
        added_files.append({
            "path": path,
            "timestamp": int(time.time()),
        })
        self.emit_data_changed()

    def replaced_file(self, path, old_path=None, diff_path=None):
        self.replaced_file_count += 1
        self.setText(self.COLUMN_REPLACED_FILE, str(self.replaced_file_count))
        added_files = self.load_from_cache("added_files")
        added_files.append({
            "path": path,
            "old_path": old_path,
            "diff_path": diff_path,
            "timestamp": int(time.time()),
        })
        self.emit_data_changed()

    def get_check_state(self):
        return self.name_widget.get_check_state()

    def set_check_state(self, state):
        self.name_widget.set_check_state(state)

    def update_checked(self):
        state = self.get_check_state()
        if not self.template_node.is_producer and state in [Qt.Checked, Qt.Unchecked]:
            self.update_checked_children(state=state)

        self.update_checked_parents()

    def update_checked_children(self, state):
        self.set_check_state(state)
        for i in range(self.childCount()):
            child = self.child(i)
            child.update_checked_children(state)

    def update_checked_parents(self, previous_state=None):
        if self.parent() is None:
            return

        if previous_state == Qt.PartiallyChecked:
            item_state = Qt.PartiallyChecked
        else:
            item_state = self.parent().get_state(only_children=True)

        if not self.parent().template_node.is_producer:
            self.parent().set_check_state(item_state)
        self.parent().update_checked_parents(item_state)

    def get_state(self, only_children=False):
        state = None
        for i in range(self.childCount()):
            child = self.child(i)
            child_state = child.get_state()
            if child_state == Qt.PartiallyChecked:
                return Qt.PartiallyChecked
            if state is None:
                state = child_state
            elif state != child_state:
                return Qt.PartiallyChecked

        if only_children:
            return state

        if state is None:
            return self.get_check_state()

        if self.get_check_state() == state:
            return state
        else:
            return Qt.PartiallyChecked


class CheckBox(QCheckBox):
    def nextCheckState(self):
        state = self.checkState()
        if state == Qt.Checked:
            self.setCheckState(Qt.Unchecked)
        else:
            self.setCheckState(Qt.Checked)


class TreeWidgetItemName(QWidget):
    LOADING_GIF_PATH = os.path.join(ASSETS_PATH, "loading.gif")
    IDLE_IMAGE_PATH = os.path.join(ASSETS_PATH, "idle.png")
    WARNING_SVG_PATH = os.path.join(ASSETS_PATH, "warning.svg")
    ERROR_SVG_PATH = os.path.join(ASSETS_PATH, "error.svg")
    SUCCESS_SVG_PATH = os.path.join(ASSETS_PATH, "success.svg")

    def __init__(self, name, icon_path, check_state, parent=None):
        super().__init__(parent=parent)
        if isinstance(check_state, int):
            if check_state == 0:
                check_state = Qt.Unchecked
            elif check_state == 1:
                check_state = Qt.PartiallyChecked
            elif check_state == 2:
                check_state = Qt.Checked
            else:
                raise ValueError
        self.check_box = CheckBox()
        self.check_box.setCheckState(check_state)
        self.check_box.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.state_check_changed = self.check_box.stateChanged

        self.text = QLabel(name)
        self.text.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        size = self.check_box.sizeHint().width()

        self.icon = DynamicIconLabel(icon_path, size, size, self)

        self.stateWidget = QStackedWidget()
        self.stateWidget.setMaximumSize(size, size)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setAlignment(Qt.AlignLeft)
        main_layout.addWidget(self.check_box)
        main_layout.addWidget(self.icon)
        main_layout.addWidget(self.text)
        main_layout.addWidget(self.stateWidget)

        self.setLayout(main_layout)

        self.loading_movie = MovieLabel(self.LOADING_GIF_PATH, size, size, self)
        self.idle_image = DynamicIconLabel(self.IDLE_IMAGE_PATH, size, size, self)
        self.warning_svg = DynamicIconLabel(self.WARNING_SVG_PATH, size, size, self)
        self.error_svg = DynamicIconLabel(self.ERROR_SVG_PATH, size, size, self)
        self.error_svg.setToolTipDuration(10000000)
        self.success_svg = DynamicIconLabel(self.SUCCESS_SVG_PATH, size, size, self)

        self.stateWidget.addWidget(self.loading_movie)
        self.stateWidget.addWidget(self.idle_image)
        self.stateWidget.addWidget(self.warning_svg)
        self.stateWidget.addWidget(self.error_svg)
        self.stateWidget.addWidget(self.success_svg)

        self.set_idle()

    def set_name(self, name):
        self.text.setText(name)

    def get_check_state(self):
        return self.check_box.checkState()

    def set_check_state(self, state):
        self.check_box.setCheckState(state)
        # Weird bug in pyinstaller. Updates check_box
        self.check_box.hide()
        self.check_box.show()

    def set_state(self, state, msg=None):
        if state == TreeWidgetItem.STATE_IDLE:
            self.set_idle()
        elif state == TreeWidgetItem.STATE_LOADING:
            self.set_loading(msg=msg)
        elif state == TreeWidgetItem.STATE_WARNING:
            self.set_warning(msg=msg)
        elif state == TreeWidgetItem.STATE_ERROR:
            self.set_error(msg=msg)
        elif state == TreeWidgetItem.STATE_SUCCESS:
            self.set_success(msg=msg)
        elif state == TreeWidgetItem.STATE_NOTHING:
            self.set_idle()

    def set_idle(self):
        self.stateWidget.hide()
        self.stateWidget.setCurrentWidget(self.idle_image)

    def set_loading(self, msg=None):
        if msg is not None:
            self.loading_movie.setToolTip(msg)
        self.stateWidget.show()
        self.stateWidget.setCurrentWidget(self.loading_movie)

    def set_error(self, msg=None):
        self.stateWidget.show()
        self.stateWidget.setCurrentWidget(self.error_svg)

        if msg is not None:
            self.error_svg.setToolTip(msg)
            if not QToolTip.isVisible() and \
                    QApplication.activeWindow() is self.window() and \
                    not self.error_svg.visibleRegion().isNull():
                QToolTip.showText(self.error_svg.mapToGlobal(QPoint(0, 0)), msg)

    def set_warning(self, msg=None):
        if msg is not None:
            self.warning_svg.setToolTip(msg)
        self.stateWidget.show()
        self.stateWidget.setCurrentWidget(self.warning_svg)

    def set_success(self, msg=None):
        if msg is not None:
            self.success_svg.setToolTip(msg)
        self.stateWidget.show()
        self.stateWidget.setCurrentWidget(self.success_svg)
