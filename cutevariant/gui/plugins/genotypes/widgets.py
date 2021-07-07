"""Plugin to Display genotypes variants 
"""
import typing

# Qt imports
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *

# Custom imports
from cutevariant.core import sql, command
from cutevariant.core.reader import BedReader
from cutevariant.gui import plugin, FIcon, style
from cutevariant.commons import logger, DEFAULT_SELECTION_NAME


LOGGER = logger()

PHENOTYPE_STR = {0: "Missing", 1: "Unaffected", 2: "Affected"}
PHENOTYPE_COLOR = {0: QColor("lightgray"), 1: QColor("green"), 2: QColor("red")}


class GenotypesModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []
        self.conn = None
        self._fields = ["gt", "ad", "gq", "pl"]

    def rowCount(self, parent: QModelIndex = QModelIndex) -> int:
        """ override """
        return len(self.items)

    def columnCount(self, parent: QModelIndex = QModelIndex) -> int:
        """override """
        return len(self._fields) + 1

    def data(self, index: QModelIndex, role: Qt.ItemDataRole) -> typing.Any:
        """override"""
        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            item = self.items[index.row()]

            if index.column() == 0:
                return item["name"]

            else:
                field = self.headerData(index.column(), Qt.Horizontal, Qt.DisplayRole)
                return item.get(field, "error")

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int
    ) -> typing.Any:

        if orientation == Qt.Horizontal and role == Qt.DisplayRole:

            if section == 0:
                return "sample"
            else:
                return self._fields[section - 1]

        return None

    def load(self, variant_id):

        if self.conn:
            self.beginResetModel()
            self.items.clear()
            self.items = list(
                sql.get_sample_annotations_by_variant(
                    self.conn, variant_id, self._fields
                )
            )

            self.endResetModel()

    def sort(self, column: int, order: Qt.SortOrder) -> None:
        pass
        # self.beginResetModel()
        # sorting_key = "phenotype" if column == 1 else "genotype"
        # self.items = sorted(
        #     self.items,
        #     key=lambda i: i[sorting_key],
        #     reverse=order == Qt.DescendingOrder,
        # )
        # self.endResetModel()

    def clear(self):
        self.beginResetModel()
        self.items = []
        self.endResetModel()


class GenotypesWidget(plugin.PluginWidget):
    """Widget displaying the list of avaible selections.
    User can select one of them to update Query::selection
    """

    ENABLE = True
    REFRESH_STATE_DATA = {"current_variant"}

    def __init__(self, parent=None, conn=None):
        """
        Args:
            parent (QWidget)
            conn (sqlite3.connexion): sqlite3 connexion
        """
        super().__init__(parent)

        self.toolbar = QToolBar()
        self.view = QTableView()
        self.view.setShowGrid(False)
        self.view.setSortingEnabled(True)
        self.model = GenotypesModel()

        self.setWindowIcon(FIcon(0xF0A8C))

        self.view.setModel(self.model)

        vlayout = QVBoxLayout()
        vlayout.setContentsMargins(0, 0, 0, 0)
        vlayout.addWidget(self.toolbar)
        vlayout.addWidget(self.view)
        self.setLayout(vlayout)

        self.view.doubleClicked.connect(self._on_double_clicked)

        self.field_action = self.toolbar.addAction("Field")

    def _create_field_menu(self):

        menu = QMenu()

        for col in range(self.model.columnCount()):
            field = self.model.headerData(col, Qt.Horizontal, Qt.DisplayRole)
            action = QAction(field)
            action.setCheckable(True)
            print(col, field)
            action.toggled.connect(
                lambda x: self.view.showColumn(col) if x else self.view.hideColumn(col)
            )

            menu.addAction(action)

        self.field_action.setMenu(menu)

    def _on_double_clicked(self, index: QModelIndex):
        sample_name = index.siblingAtColumn(0).data()
        if sample_name:
            # samples['NA12877'].gt > 1
            self.mainwindow.set_state_data(
                "filters", {"$and": [{f"samples.{sample_name}.gt": {"$gte": 1}}]}
            )
            self.mainwindow.refresh_plugins(sender=None)

    def on_open_project(self, conn):
        self.model.conn = conn
        self.model.clear()
        self.model.load(1)

        self._create_field_menu()

    def on_refresh(self):
        self.current_variant = self.mainwindow.get_state_data("current_variant")
        variant_id = self.current_variant["id"]

        self.model.load(variant_id)

        self.view.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.view.setSelectionBehavior(QAbstractItemView.SelectRows)


if __name__ == "__main__":

    import sqlite3
    import sys
    from PySide2.QtWidgets import QApplication

    app = QApplication(sys.argv)

    conn = sqlite3.connect("/DATA/dev/cutevariant/corpos2.db")
    conn.row_factory = sqlite3.Row

    view = GenotypesWidget()
    view.on_open_project(conn)
    view.show()

    app.exec_()
