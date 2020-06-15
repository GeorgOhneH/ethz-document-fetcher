from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtSvg import QSvgWidget

import os
import logging

from core.exceptions import ParseTemplateError
from core import template_parser
from settings import settings

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


class ViewTreeItemWidget(QWidget):
    LOADING_GIF_PATH = "gui/images/loading.gif"
    IDLE_IMAGE_PATH = "gui/images/idle.png"
    WARNING_SVG_PATH = "gui/images/warning.svg"
    ERROR_SVG_PATH = "gui/images/error.svg"
    SUCCESS_SVG_PATH = "gui/images/success.svg"

    STATE_IDLE = 0
    STATE_LOADING = 1
    STATE_ERROR = 2
    STATE_WARNING = 3
    STATE_SUCCESS = 4

    def __init__(self, template_node, parent=None):
        super().__init__(parent=parent)
        self.loading_count = 0
        self.state = None
        self.template_node = template_node
        self.children = []
        self.custom_parent = None

        self.text = QLabel()
        self.text.setText(template_node.gui_name())
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
        self.loading_count = 0
        self.state = self.STATE_IDLE
        self.stateWidget.hide()
        self.stateWidget.setCurrentWidget(self.idle_image)

    def set_loading(self, msg=None):
        self.loading_count += 1
        if msg is not None:
            self.loading_movie.setToolTip(msg)
        self.state = self.STATE_LOADING
        self.stateWidget.show()
        self.stateWidget.setCurrentWidget(self.loading_movie)

    def set_error(self, msg=None):
        self.loading_count = 0
        if msg is not None:
            self.error_svg.setToolTip(msg)
        self.state = self.STATE_ERROR
        self.stateWidget.show()
        self.stateWidget.setCurrentWidget(self.error_svg)

    def set_warning(self, msg=None):
        self.loading_count = 0
        if msg is not None:
            self.warning_svg.setToolTip(msg)
        self.state = self.STATE_WARNING
        self.stateWidget.show()
        self.stateWidget.setCurrentWidget(self.warning_svg)

    def set_success(self, msg=None):
        self.loading_count -= 1
        if self.loading_count == 0:
            if msg is not None:
                self.success_svg.setToolTip(msg)
            self.state = self.STATE_SUCCESS
            self.stateWidget.show()
            self.stateWidget.setCurrentWidget(self.success_svg)

    def add_child(self, child):
        self.children.append(child)
        if child.custom_parent is not None:
            raise ValueError("Child already has a parent")
        child.custom_parent = self


class TemplateViewTree(QTreeWidget):
    base_path_updated = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent=parent)
        self.override_widgets = {}
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.prepare_menu)
        self.template = template_parser.Template(settings.template_path)
        try:
            self.template.load()
        except Exception as e:
            error_dialog = QErrorMessage(self)
            error_dialog.showMessage(f"Error while loading the file. Error: {e}")
        self.init_view_tree()

    @pyqtSlot(str, str)
    def update_folder_name(self, unique_key, folder_name):
        logger.debug(f"{unique_key} folder_name got updated to {folder_name}")
        self.override_widgets[unique_key].text.setText(folder_name)

    @pyqtSlot(str, str)
    def update_base_path(self, unique_key, base_path):
        logger.debug(f"{unique_key} base_path got updated to {base_path}")
        self.override_widgets[unique_key].template_node.base_path = base_path
        self.base_path_updated.emit()

    @pyqtSlot(str)
    @pyqtSlot(str, str)
    def site_started(self, unique_key, msg=None):
        self.override_widgets[unique_key].set_loading(msg)

    @pyqtSlot(str)
    @pyqtSlot(str, str)
    def site_finished_successful(self, unique_key, msg=None):
        widget = self.override_widgets[unique_key]
        widget.set_success(msg)

    @pyqtSlot(str)
    @pyqtSlot(str, str)
    def site_quit_with_warning(self, unique_key, msg=None):
        widget = self.override_widgets[unique_key]
        widget.set_warning(msg)

    @pyqtSlot(str)
    @pyqtSlot(str, str)
    def site_quit_with_error(self, unique_key, msg=None):
        widget = self.override_widgets[unique_key]
        widget.set_error(msg)

    def reset_widgets(self):
        for key, widget in self.override_widgets.items():
            widget.set_idle()

    def stop_widgets(self):
        for key, widget in self.override_widgets.items():
            if widget.state == widget.STATE_LOADING:
                widget.set_warning("Interrupted by user")

    def quit_widgets(self):
        for key, widget in self.override_widgets.items():
            if widget.state == widget.STATE_LOADING:
                widget.set_error("Site did not give a finish Signal. (You should never see this message)")

    def add_item_widget(self, template_node, unique_key, widget_parent=None, override_widget_parent=None):
        widget = QTreeWidgetItem()
        if widget_parent is None:
            self.addTopLevelItem(widget)
        else:
            widget_parent.addChild(widget)
        widget.setExpanded(True)
        override_widget = ViewTreeItemWidget(template_node)
        widget.override_widget = override_widget
        if override_widget_parent is not None:
            override_widget_parent.add_child(override_widget)

        self.override_widgets[unique_key] = override_widget
        self.setItemWidget(widget, 0, override_widget)
        return widget, override_widget

    def prepare_menu(self, point):
        widget = self.itemAt(point).override_widget
        menu = QMenu(self)

        run_action = menu.addAction("Run recursive")
        run_action.setEnabled(not self.parent().thread.isRunning())
        if self.parent().thread.isRunning():
            self.parent().thread.finished.connect(lambda: run_action.setEnabled(True))
        run_action.triggered.connect(lambda: self.parent().start_thread(widget.template_node.unique_key, True))

        run_action = menu.addAction("Run")
        run_action.setEnabled(not self.parent().thread.isRunning())
        if self.parent().thread.isRunning():
            self.parent().thread.finished.connect(lambda: run_action.setEnabled(True))
        run_action.triggered.connect(lambda: self.parent().start_thread(widget.template_node.unique_key, False))

        menu.addSeparator()

        open_folder_action = menu.addAction("Open Folder")
        if widget.template_node.base_path is not None:
            base_path = os.path.join(settings.base_path, widget.template_node.base_path)
            if not os.path.exists(base_path):
                open_folder_action.setEnabled(False)
            url = QUrl.fromLocalFile(base_path)
            open_folder_action.triggered.connect(lambda: QDesktopServices.openUrl(url))
        else:
            open_folder_action.setEnabled(False)

        menu.exec_(self.mapToGlobal(point))

    def init_view_tree(self):
        if self.template.root.folder is not None:
            self.init_widgets(self.template.root.folder, parents=(None, None))
        for site in self.template.root.sites:
            self.init_widgets(site, parents=(None, None))

    def init_widgets(self, node, parents):
        widgets = self.add_item_widget(node, node.unique_key, *parents)

        if node.folder is not None:
            self.init_widgets(node.folder, parents=widgets)
        for site in node.sites:
            self.init_widgets(site, parents=widgets)
