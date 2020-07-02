import logging
import time
import os

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import *

from core.storage import cache
from gui.constants import ASSETS_PATH

logger = logging.getLogger(__name__)


class SVGWidget(QSvgWidget):
    def __init__(self, path, width, height, parent):
        super().__init__(parent=parent)
        self.load(path)
        self.setFixedSize(width, height)


class ImageLabel(QLabel):
    def __init__(self, path, width, height, parent=None):
        super().__init__(parent=parent)
        self.image = QPixmap(path)
        self.image = self.image.scaled(width, height)
        self.setFixedSize(width, height)
        self.setPixmap(self.image)


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


class TreeWidgetItemSignals(QObject):
    data_changed = pyqtSignal(object)


class TreeWidgetItem(QTreeWidgetItem):
    STATE_NOTHING = 0
    STATE_IDLE = 1
    STATE_LOADING = 2
    STATE_ERROR = 3
    STATE_WARNING = 4
    STATE_SUCCESS = 5

    COLUMN_NAME = 0
    COLUMN_STATE = 1
    COLUMN_ADDED_FILE = 2
    COLUMN_REPLACED_FILE = 3
    COLUMN_EMPTY = 4

    def __init__(self, template_node, controller):
        super().__init__()
        self.template_node = template_node
        self.controller = controller
        self.signals = TreeWidgetItemSignals()
        self.state_widget = TreeWidgetItemState()

        self.added_new_file_count = 0
        self.replaced_file_count = 0

        self.active_item_count = 0
        self.state = self.STATE_NOTHING
        self.children = []
        self.custom_parent = None

        self.controller.settings_dialog.accepted.connect(self.emit_data_changed)

    def init_widgets(self):
        self.setText(self.COLUMN_NAME, self.template_node.get_gui_name())
        self.setIcon(self.COLUMN_NAME, self.template_node.get_gui_icon())
        self.setCheckState(self.COLUMN_NAME, self.template_node.meta_data.get("check_state", Qt.Checked))
        self.setExpanded(True)
        if not self.template_node.is_producer:
            return
        self.treeWidget().setItemWidget(self, self.COLUMN_STATE, self.state_widget)
        self._set_state(self.STATE_IDLE)
        self.setText(self.COLUMN_ADDED_FILE, str(self.added_new_file_count))
        self.setTextAlignment(self.COLUMN_ADDED_FILE, Qt.AlignRight | Qt.AlignVCenter)
        self.setText(self.COLUMN_REPLACED_FILE, str(self.replaced_file_count))
        self.setTextAlignment(self.COLUMN_REPLACED_FILE, Qt.AlignRight | Qt.AlignVCenter)

    def load_from_cache(self, name):
        if self.controller.site_settings.base_path is None:
            return []
        path_name = self.controller.site_settings.base_path.replace("\\", "").replace("/", "").replace(":", "").replace(
            ".", "")
        json = cache.get_json(name + path_name)
        if self.template_node.unique_key not in json:
            result = []
            json[self.template_node.unique_key] = result
            return result

        return json[self.template_node.unique_key]

    def emit_data_changed(self):
        self.signals.data_changed.emit(self)

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

    def _set_state(self, state):
        self.state = state
        self.emit_data_changed()

    def set_idle(self):
        self.active_item_count = 0
        self._set_state(self.STATE_IDLE)
        self.state_widget.set_idle()

    def set_loading(self, msg=None):
        self.active_item_count += 1
        self._set_state(self.STATE_LOADING)
        self.state_widget.set_loading(msg)

    def set_error(self, msg=None):
        self._set_state(self.STATE_ERROR)
        self.state_widget.set_error(msg)

    def set_warning(self, msg=None):
        self._set_state(self.STATE_WARNING)
        self.state_widget.set_warning(msg)

    def set_success(self, msg=None):
        self.active_item_count -= 1
        if self.active_item_count < 0:
            logger.warning("Active count is negative")
        if self.active_item_count == 0 and self.state not in [self.STATE_ERROR, self.STATE_WARNING]:
            self._set_state(self.STATE_SUCCESS)
            self.state_widget.set_success(msg)

    def set_folder_name(self, folder_name):
        self.template_node.folder_name = folder_name
        self.setText(self.COLUMN_NAME, folder_name)
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

    def replaced_file(self, path, old_path=None):
        self.replaced_file_count += 1
        self.setText(self.COLUMN_REPLACED_FILE, str(self.replaced_file_count))
        added_files = self.load_from_cache("added_files")
        added_files.append({
            "path": path,
            "old_path": old_path,
            "timestamp": int(time.time()),
        })
        self.emit_data_changed()

    def update_checked(self):
        state = self.checkState(self.COLUMN_NAME)
        if not self.template_node.is_producer and state in [Qt.Checked, Qt.Unchecked]:
            self.update_checked_children(state=state)

        self.update_checked_parents()

    def update_checked_children(self, state):
        self.setCheckState(self.COLUMN_NAME, state)
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
            self.parent().setCheckState(self.COLUMN_NAME, item_state)
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
            return self.checkState(self.COLUMN_NAME)

        if self.checkState(self.COLUMN_NAME) == state:
            return state
        else:
            return Qt.PartiallyChecked


class TreeWidgetItemState(QWidget):
    LOADING_GIF_PATH = os.path.join(ASSETS_PATH, "loading.gif")
    IDLE_IMAGE_PATH = os.path.join(ASSETS_PATH, "idle.png")
    WARNING_SVG_PATH = os.path.join(ASSETS_PATH, "warning.svg")
    ERROR_SVG_PATH = os.path.join(ASSETS_PATH, "error.svg")
    SUCCESS_SVG_PATH = os.path.join(ASSETS_PATH, "success.svg")

    def __init__(self, state=TreeWidgetItem.STATE_IDLE, parent=None):
        super().__init__(parent=parent)
        self.text = QLabel(TreeWidgetItem.state_to_string(state))
        self.text.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        size = self.text.minimumSizeHint().height()

        self.stateWidget = QStackedWidget()
        self.stateWidget.setMaximumSize(size, size)

        main_layout = QHBoxLayout()
        main_layout.setAlignment(Qt.AlignLeft)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.addWidget(self.stateWidget)
        main_layout.addWidget(self.text)

        self.setLayout(main_layout)

        self.loading_movie = MovieLabel(self.LOADING_GIF_PATH, size, size, self)
        self.idle_image = ImageLabel(self.IDLE_IMAGE_PATH, size, size, self)
        self.warning_svg = SVGWidget(self.WARNING_SVG_PATH, size, size, self)
        self.error_svg = SVGWidget(self.ERROR_SVG_PATH, size, size, self)
        self.success_svg = SVGWidget(self.SUCCESS_SVG_PATH, size, size, self)

        self.stateWidget.addWidget(self.loading_movie)
        self.stateWidget.addWidget(self.idle_image)
        self.stateWidget.addWidget(self.warning_svg)
        self.stateWidget.addWidget(self.error_svg)
        self.stateWidget.addWidget(self.success_svg)

        self.set_idle()

    def set_idle(self):
        self.stateWidget.hide()
        self.stateWidget.setCurrentWidget(self.idle_image)
        self.text.setText(TreeWidgetItem.state_to_string(TreeWidgetItem.STATE_IDLE))

    def set_loading(self, msg=None):
        if msg is not None:
            self.loading_movie.setToolTip(msg)
        self.stateWidget.show()
        self.stateWidget.setCurrentWidget(self.loading_movie)
        self.text.setText(TreeWidgetItem.state_to_string(TreeWidgetItem.STATE_LOADING))

    def set_error(self, msg=None):
        if msg is not None:
            self.error_svg.setToolTip(msg)
        self.stateWidget.show()
        self.stateWidget.setCurrentWidget(self.error_svg)
        self.text.setText(TreeWidgetItem.state_to_string(TreeWidgetItem.STATE_ERROR))

    def set_warning(self, msg=None):
        if msg is not None:
            self.warning_svg.setToolTip(msg)
        self.stateWidget.show()
        self.stateWidget.setCurrentWidget(self.warning_svg)
        self.text.setText(TreeWidgetItem.state_to_string(TreeWidgetItem.STATE_WARNING))

    def set_success(self, msg=None):
        if msg is not None:
            self.success_svg.setToolTip(msg)
        self.stateWidget.show()
        self.stateWidget.setCurrentWidget(self.success_svg)
        self.text.setText(TreeWidgetItem.state_to_string(TreeWidgetItem.STATE_SUCCESS))
