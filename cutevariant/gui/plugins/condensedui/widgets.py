import enum
from poc.harmonizomeapi import Enum
from cutevariant.core import querybuilder

from cutevariant.gui.ficon import FIcon
import sqlite3
import typing

from PySide2.QtCore import (
    QLine,
    Qt,
    QAbstractListModel,
    QAbstractTableModel,
    QModelIndex,
    QObject,
    QStringListModel,
    Signal,
)
from PySide2.QtWidgets import (
    QAction,
    QCheckBox,
    QComboBox,
    QCompleter,
    QFormLayout,
    QGraphicsSceneHoverEvent,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QTableView,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from cutevariant.core import sql

from cutevariant.gui import plugin
from cutevariant.gui import MainWindow

from cutevariant.gui.plugins.source_editor.widgets import SourceModel
from cutevariant.gui.plugins.fields_editor.widgets import FieldsPresetModel
from cutevariant.gui.plugins.filters_editor.widgets import FiltersPresetModel

from cutevariant.gui.plugins.group_by_view.widgets import GroupbyModel

from cutevariant.gui.widgets.searchable_table_widget import LoadingTableView


class PresetsGroup(QGroupBox):

    # Just tell anyone interested that one preset changed. It is up to receiver to make anythig out of it
    # For example, call²
    presets_changed = Signal()

    def __init__(self, title: str, parent: QWidget) -> None:
        super().__init__(title, parent=parent)

        self._conn = None

        self.combo_source = QComboBox(self)
        self.source_model = SourceModel()
        self.combo_source.setModel(self.source_model)

        self.combo_fields = QComboBox(self)
        self.fields_model = FieldsPresetModel(parent=self)
        self.combo_fields.setModel(self.fields_model)

        self.combo_filters = QComboBox(self)
        self.filters_model = FiltersPresetModel(parent=self)
        self.combo_filters.setModel(self.filters_model)

        main_layout = QFormLayout(self)
        main_layout.addRow(self.tr("Source"), self.combo_source)
        main_layout.addRow(self.tr("Fields"), self.combo_fields)
        main_layout.addRow(self.tr("Filters"), self.combo_filters)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.combo_source.currentTextChanged.connect(self.presets_changed)
        self.combo_fields.currentTextChanged.connect(self.presets_changed)
        self.combo_filters.currentTextChanged.connect(self.presets_changed)

        self.load()

    def load(self):
        """Update the state of internal models"""
        self.fields_model.load()
        self.filters_model.load()
        self.source_model.load()

    def set_conn(self, conn: sqlite3.Connection):
        self._conn = conn
        self.source_model.conn = conn
        self.source_model.load()

    def update_query(self, fields: list, filters: dict, source: str):
        """[summary]

        Args:
            fields (list): Fields to update
            filters (dict): Filters to update
            source (str): Source to query from

        Returns:
            [type]: Copies of fields,filters,source
        """
        fields = fields.copy()
        filters = filters.copy()

        fields = self.fields_model.data(
            self.fields_model.index(self.combo_fields.currentIndex()), Qt.UserRole
        )
        filters = self.filters_model.data(
            self.filters_model.index(self.combo_filters.currentIndex()), Qt.UserRole
        )

        source = self.combo_source.currentText()

        return fields, filters, source


class ACMGButtons(QWidget):
    """Widget to input list of ACMG classification criteria.
    Emits acmg_changed signal when the list changes.
    Member selected_classification is a list of booleans indicating chosen criteria
    """

    acmg_changed = Signal()

    ACMG_ICON = {
        0: FIcon(0xF03A1, "lightgray"),
        1: FIcon(0xF03A4, "#71e096"),
        2: FIcon(0xF03A7, "#a7ecbe"),
        3: FIcon(0xF03AA, "#f5a26f"),
        4: FIcon(0xF03AD, "#f9cdd1"),
        5: FIcon(0xF03B1, "#ed6d79"),
    }

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        classifications = [
            "Unclassified",
            "Benin",
            "Likely benin",
            "Variant of uncertain significance",
            "Likely pathogen",
            "Pathogen",
        ]
        self.label = QLabel(self.tr("ACMG classification"), self)

        self.toolbar = QToolBar(parent=self)
        self.toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)
        for i, cl in enumerate(classifications):
            action: QAction = self.toolbar.addAction("")
            action.setToolTip(cl)
            action.setData(i)
            action.setIcon(self.__class__.ACMG_ICON.get(i))
            action.setCheckable(True)
            action.setChecked(True)
            action.toggled.connect(self._on_classification_toggled)
            button = self.toolbar.widgetForAction(action)
            button.setStyleSheet("background-color: white;")
            button.setAutoRaise(False)

        main_layout.addWidget(self.label)
        main_layout.addWidget(self.toolbar)

        # Default to all selected
        self.selected_classifications = [True, True, True, True, True, True]

    def _on_classification_toggled(self, checked=False):
        act: QAction = self.sender()
        i = int(act.data())
        self.selected_classifications[i] = checked
        self.acmg_changed.emit()


class ValidationGroup(QGroupBox):

    # Tell whenever one of the validation fields changes
    validation_crit_changed = Signal()

    def __init__(self, title: str, parent: QWidget) -> None:
        super().__init__(title, parent=parent)

        self.checkbox_fav = QCheckBox(self.tr("Show favorites only"), self)
        self.buttons_acmg = ACMGButtons(self)

        self.checkbox_fav.toggled.connect(self.validation_crit_changed)
        self.buttons_acmg.acmg_changed.connect(self.validation_crit_changed)

        self.le_tags_include = QLineEdit(self)
        self.le_tags_include.setPlaceholderText(
            self.tr("Tags to include (comma separated)")
        )
        self.le_tags_exclude = QLineEdit(self)
        self.le_tags_exclude.setPlaceholderText(
            self.tr("Tags to exclude (comma separated)")
        )
        self.le_comments_search = QLineEdit(self)
        self.le_comments_search.setPlaceholderText(self.tr("Search in comments"))

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.checkbox_fav)
        main_layout.addWidget(self.buttons_acmg)
        main_layout.addWidget(self.le_tags_include)
        main_layout.addWidget(self.le_tags_exclude)
        main_layout.addWidget(self.le_comments_search)

    def update_query(self, fields: list, filters: dict, source: str):
        fields = fields.copy()
        filters = filters.copy()

        if "$and" not in filters:
            filters["$and"] = []

        # Add favorite filter if checked
        if self.checkbox_fav.isChecked():
            filters["$and"].append({"favorite": True})

        # Add them if they are not all selected
        if not all(self.buttons_acmg.selected_classifications):

            condition = {
                "classification": {
                    "$in": [
                        i
                        for i, cl in enumerate(
                            self.buttons_acmg.selected_classifications
                        )
                        if cl
                    ]
                }
            }
            if any(self.buttons_acmg.selected_classifications):
                for index, cond in enumerate(filters["$and"]):
                    if list(cond.keys())[0] == list(condition.keys())[0]:
                        filters["$and"][index] = condition
                        break
                else:
                    filters["$and"].append(condition)

        if self.le_tags_include.text():
            filters["$and"].append(
                {
                    "$or": [
                        {"tags": {"$has": tag}}
                        for tag in self.le_tags_include.text().split(",")
                    ]
                }
            )
        # TODO Tags exclude
        if self.le_comments_search.text():
            filters["$and"].append(
                {"comment": {"$regex": self.le_comments_search.text()}}
            )

        return fields, filters, source


class GroupByAnnotation(QGroupBox):
    """Display unique values for a given field (except for sample values)"""

    def __init__(self, title: str, parent: QWidget) -> None:
        super().__init__(title, parent=parent)

        self.field_combo = QComboBox(self)
        self.fields_model = QStringListModel([], self)
        self.field_combo.setModel(self.fields_model)
        self.field_combo.currentTextChanged.connect(self.load)

        self.groupby_model = GroupbyModel(self)
        self.groupby_view = LoadingTableView(self)
        self.groupby_view.setModel(self.groupby_model)
        self.groupby_model.groupby_started.connect(self.start_loading)
        self.groupby_model.groubpby_finished.connect(self.stop_loading)

        self.fields = []
        self.current_source = "variants"
        self.current_filters = {}
        self._conn = None

        main_layout = QFormLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        main_layout.addRow(self.tr("Unique values"), self.field_combo)
        main_layout.addWidget(self.groupby_view)

    def start_loading(self):
        self.groupby_view.start_loading()

    def stop_loading(self):
        self.groupby_view.stop_loading()
        self.groupby_view.horizontalHeader().setStretchLastSection(False)
        self.groupby_view.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Stretch
        )
        self.groupby_view.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeToContents
        )

    def load(self):
        self.groupby_model.load(
            self.field_combo.currentText(),
            self.fields,
            self.current_source,
            self.current_filters,
        )

    def set_conn(self, conn: sqlite3.Connection):
        self._conn = conn
        if self._conn:
            self.fields = [
                field["name"]
                for field in sql.get_field_by_category(self._conn, "variants")
            ] + [
                f"ann.{field['name']}"
                for field in sql.get_field_by_category(self._conn, "annotations")
            ]
            self.fields_model.setStringList(self.fields)
            self.groupby_model.set_conn(conn)


class CondenseduiWidget(plugin.PluginWidget):

    # Location of the plugin in the mainwindow
    # Can be : DOCK_LOCATION, CENTRAL_LOCATION, FOOTER_LOCATION
    LOCATION = plugin.DOCK_LOCATION
    # Make the plugin enable. Otherwise, it will be not loaded
    ENABLE = True

    # Refresh the plugin only if the following state variable changed.
    # Can be : fields, filters, source

    REFRESH_STATE_DATA = {"fields", "filters", "source"}

    def __init__(self, parent=None):
        super().__init__(parent)

        self.preset_group = PresetsGroup(self.tr("Presets"), self)
        self.valid_group = ValidationGroup(self.tr("Validation criteria"), self)
        self.groupby = GroupByAnnotation(self.tr("Field unique values"), self)

        self.preset_group.presets_changed.connect(self.update_query)
        self.valid_group.validation_crit_changed.connect(self.update_query)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.preset_group)
        main_layout.addWidget(self.valid_group)
        main_layout.addWidget(self.groupby)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.fields, self.filters, self.source = list(), dict(), str()

        self.preset_group.presets_changed.connect(self.update_query)
        self.valid_group.validation_crit_changed.connect(self.update_query)

    def on_register(self, mainwindow: MainWindow):
        """This method is called when the plugin is registered from the mainwindow.

        This is called one time at the application startup.

        Args:
            mainwindow (MainWindow): cutevariant Mainwindow
        """
        self.mainwindow = mainwindow

    def on_open_project(self, conn: sqlite3.Connection):
        """This method is called when a project is opened

                Do your initialization here.
        You may want to store the conn variable to use it later.

        Args:
            conn (sqlite3.connection): A connection to the sqlite project
        """
        self.preset_group.set_conn(conn)
        self.groupby.set_conn(conn)
        self.on_refresh()

    def on_refresh(self):
        """This method is called from mainwindow.refresh_plugins()

        You may want to overload this method to update the plugin state
        when query changed
        """
        self.preset_group.load()
        self.groupby.load()

    def update_query(self):
        """Updates query using all criteria from self's widgets"""
        self.fields, self.filters, self.source = self.preset_group.update_query(
            self.fields, self.filters, self.source
        )
        self.fields, self.filters, self.source = self.valid_group.update_query(
            self.fields, self.filters, self.source
        )
        self.groupby.current_filters = self.filters
        self.groupby.current_source = self.source
        self.groupby.load()

        self.mainwindow.set_state_data("fields", self.fields)
        self.mainwindow.set_state_data("filters", self.filters)
        self.mainwindow.set_state_data("source", self.source)
        self.mainwindow.refresh_plugins(sender=self)
