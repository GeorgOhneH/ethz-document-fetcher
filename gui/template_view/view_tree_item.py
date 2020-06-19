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


class TreeWidgetItemName(QWidget):
    LOADING_GIF_PATH = os.path.join(ASSETS_PATH, "loading.gif")
    IDLE_IMAGE_PATH = os.path.join(ASSETS_PATH, "idle.png")
    WARNING_SVG_PATH = os.path.join(ASSETS_PATH, "warning.svg")
    ERROR_SVG_PATH = os.path.join(ASSETS_PATH, "error.svg")
    SUCCESS_SVG_PATH = os.path.join(ASSETS_PATH, "success.svg")

    def __init__(self, text, parent=None):
        super().__init__(parent=parent)
        self.text = QLabel()
        self.text.setText(text)
        self.text.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        size = self.text.minimumSizeHint().height()

        self.stateWidget = QStackedWidget()
        self.stateWidget.setMaximumSize(size, size)

        main_layout = QHBoxLayout()
        main_layout.setAlignment(Qt.AlignLeft)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.addWidget(self.text)
        main_layout.addWidget(self.stateWidget)

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

    def set_loading(self, msg=None):
        if msg is not None:
            self.loading_movie.setToolTip(msg)
        self.stateWidget.show()
        self.stateWidget.setCurrentWidget(self.loading_movie)

    def set_error(self, msg=None):
        if msg is not None:
            self.error_svg.setToolTip(msg)
        self.stateWidget.show()
        self.stateWidget.setCurrentWidget(self.error_svg)

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


class TreeWidgetItemSignals(QObject):
    data_changed = pyqtSignal(object)


class TreeWidgetItem(QTreeWidgetItem):
    STATE_IDLE = 0
    STATE_LOADING = 1
    STATE_ERROR = 2
    STATE_WARNING = 3
    STATE_SUCCESS = 4

    COLUMN_NAME = 0
    COLUMN_ADDED_FILE = 1
    COLUMN_REPLACED_FILE = 2
    COLUMN_STATE = 3

    def __init__(self, template_node):
        super().__init__()
        self.template_node = template_node
        self.signals = TreeWidgetItemSignals()
        self.name_widget = TreeWidgetItemName(template_node.get_gui_name())

        self.added_new_file_count = 0
        self.replaced_file_count = 0

        self.added_files = self.load_from_cache("added_files")

        self.active_item_count = 0
        self.state = None
        self.children = []
        self.custom_parent = None

    def init_widgets(self):
        self.treeWidget().setItemWidget(self, self.COLUMN_NAME, self.name_widget)
        self.setIcon(self.COLUMN_NAME, self.template_node.get_gui_icon())
        self.setExpanded(True)
        self._set_state(self.STATE_IDLE)
        self.setText(self.COLUMN_ADDED_FILE, str(self.added_new_file_count))
        self.setTextAlignment(self.COLUMN_ADDED_FILE, Qt.AlignRight)
        self.setText(self.COLUMN_REPLACED_FILE, str(self.replaced_file_count))
        self.setTextAlignment(self.COLUMN_REPLACED_FILE, Qt.AlignRight)

    def load_from_cache(self, name):
        json = cache.get_json(name)
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
        else:
            raise ValueError("Not valid state")

    def state_text(self):
        return self.state_to_string(self.state)

    def _set_state(self, state):
        self.state = state
        self.setText(self.COLUMN_STATE, self.state_to_string(state))
        self.emit_data_changed()

    def set_idle(self):
        self.active_item_count = 0
        self._set_state(self.STATE_IDLE)
        self.name_widget.set_idle()

    def set_loading(self, msg=None):
        self.active_item_count += 1
        self._set_state(self.STATE_LOADING)
        self.name_widget.set_loading(msg)

    def set_error(self, msg=None):
        self.active_item_count = 0
        self._set_state(self.STATE_ERROR)
        self.name_widget.set_error(msg)

    def set_warning(self, msg=None):
        self.active_item_count = 0
        self._set_state(self.STATE_WARNING)
        self.name_widget.set_warning(msg)

    def set_success(self, msg=None):
        self.active_item_count -= 1
        if self.active_item_count < 0:
            logger.warning("Active count is negative")
        if self.active_item_count == 0:
            self._set_state(self.STATE_SUCCESS)
            self.name_widget.set_success(msg)

    def set_folder_name(self, folder_name):
        self.template_node.folder_name = folder_name
        self.name_widget.text.setText(folder_name)
        self.emit_data_changed()

    def set_base_path(self, base_path):
        self.template_node.base_path = base_path
        self.emit_data_changed()

    def added_new_file(self, path):
        self.added_new_file_count += 1
        self.setText(self.COLUMN_ADDED_FILE, str(self.added_new_file_count))
        self.added_files.append({
            "path": path,
            "timestamp": int(time.time()),
        })
        self.emit_data_changed()

    def replaced_file(self, path, old_path=None):
        self.replaced_file_count += 1
        self.setText(self.COLUMN_REPLACED_FILE, str(self.replaced_file_count))
        self.added_files.append({
            "path": path,
            "old_path": old_path,
            "timestamp": int(time.time()),
        })
        self.emit_data_changed()
