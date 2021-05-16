## ================= Settings widgets ===================
# Qt imports
from PySide2.QtCore import *
from PySide2.QtGui import QStandardItem, QStandardItemModel
from PySide2.QtWidgets import *

# Custom imports
from cutevariant.gui.plugin import PluginSettingsWidget
from cutevariant.gui.settings import AbstractSettingsWidget
from cutevariant.gui import FIcon
import cutevariant.commons as cm

import sqlite3
import os
import gzip

import glob

import typing


def zipped_text_to_sqlite(ref_filename: str, db_filename: str):
    """Converts a zipped text file (.txt.gz) with genomic annotation data into a sqlite3 database

    Args:
        ref_filename (str): File name of the zipped text file containing the genomic annotation data
        db_filename (str): Path to save the database to

    Raises:
        FileNotFoundError: If ref_filename is not a path to an existing file
    """

    # Create databases
    conn = sqlite3.connect(db_filename)

    if not os.path.isfile(ref_filename):
        raise FileNotFoundError("%s : No such file or directory !")

    conn.execute(
        """
        CREATE TABLE annotations(  
        id INTEGER PRIMARY KEY,
        transcript_name TEXT, 
        tx_start INTEGER, 
        tx_end INTEGER,
        cds_start INTEGER,
        cds_end INTEGER,
        exon_starts TEXT,
        exon_ends TEXT,
        gene TEXT
        )

    """
    )

    data = []
    with gzip.open(ref_filename, "rb") as file:
        for index, line in enumerate(file):
            if line:
                line = line.decode("utf-8").strip().split("\t")

                transcript = line[1]
                txStart = line[4]
                txEnd = line[5]
                cdsStart = line[6]
                cdsEnd = line[7]
                exonStarts = line[9]
                exonEnds = line[10]
                gene = line[12]

                data.append(
                    (
                        None,
                        transcript,
                        txStart,
                        txEnd,
                        cdsStart,
                        cdsEnd,
                        exonStarts,
                        exonEnds,
                        gene,
                    )
                )

    conn.executemany("INSERT INTO annotations VALUES(?,?,?,?,?,?,?,?,?);", data)
    conn.commit()


def open_link(url: typing.Union[QUrl, str]):
    if isinstance(url, QUrl):
        if url.toString() == "#annotation-reference-database-guidelines":
            dialog = GuidelinesDialog()
            dialog.exec_()
    elif isinstance(url, str):
        if url == "#annotation-reference-database-guidelines":
            dialog = GuidelinesDialog()
            dialog.exec_()


class GuidelinesDialog(QDialog):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent=parent)
        self.text_browser = QTextBrowser(self)
        self.text_browser.setReadOnly(True)
        self.text_browser.setMarkdown(
            self.tr(
                """## Annotation reference database guidelines
Every file with a db extension in the annotations reference folder **must** comply with the following guidelines:
<br>- Be a sqlite3 database file</br>
<br>- Contain at least one table named 'annotations'</br>
<br>- Follow this schema for the 'annotations' table:</br>
```sql
CREATE TABLE annotations (
        id INTEGER PRIMARY KEY,
        transcript_name TEXT, 
        tx_start INTEGER, 
        tx_end INTEGER,
        cds_start INTEGER,
        cds_end INTEGER,
        exon_starts TEXT,
        exon_ends TEXT,
        gene TEXT
        )
```
"""
            )
        )
        layout = QVBoxLayout(self)
        layout.addWidget(self.text_browser)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok, self)
        layout.addWidget(self.button_box)
        self.button_box.accepted.connect(self.accept)


# class AnnRefDatabaseCreator(QDialog):
#     """Dialog that ensures that the user creates a valid annotation reference database.
#     This dialog should be called whenever the user clicks the 'Add' button in the AnnRefDatabase geneviewer setting.
#     """

#     def __init__(self, parent: typing.Optional[QWidget], f: Qt.WindowFlags) -> None:
#         super().__init__(parent=parent, f=f)

#         self.instructions_label = QTextBrowser(self)
#         self.instructions_label.setTextFormat(Qt.MarkdownText)
#         self.instructions_label.setText(
#             self.tr(
#                 """You are about to add an annotations reference database to the gene viewer.
# You can either generate it from a zipped text file, or you can choose to copy an existing db file into the selected directory.
# Note, though, that every db file in the annotations reference database folder <b>must<b/> follow these <a href='#annotation-reference-database-guidelines'>guidelines</a>"""
#             )
#         )

#         self.instructions_label.linkActivated.connect(open_link)


class AnnRefListModel(QStandardItemModel):
    def load(self, folder_path: str):
        """Fills the model with list of available annotation reference databases

        Args:
            folder_path (str): Path to the folder containing annotation reference databases
        """
        if not os.path.isdir(folder_path):
            raise FileNotFoundError("%s does not name a directory", folder_path)

        self.clear()
        files = glob.glob(f"{folder_path}/*.db")
        for fn in files:
            item = QStandardItem(os.path.basename(fn).split(".")[0])
            item.setIcon(FIcon(0xF01BC))
            item.setData(fn)
            self.appendRow([item])


class AnnRefImportDialog(QDialog):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.label = QLabel(self)
        self.label.setTextFormat(Qt.MarkdownText)
        self.label.setText(
            self.tr(
                """Using this dialog you will import an existing
        """
            )
        )


class AnnRefDatabaseSettings(AbstractSettingsWidget):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(FIcon(0xF0D01))
        self.setWindowTitle(self.tr("Annotation reference databases"))

        self._database_folder_path = QDir.homePath()
        self.line_edit_database_folder_path = QLineEdit(self)
        self.line_edit_database_folder_path.setPlaceholderText(
            self.tr("Annotation reference databases folder")
        )
        self.choose_db_folder_act = self.line_edit_database_folder_path.addAction(
            FIcon(0xF0770), QLineEdit.TrailingPosition
        )
        self.choose_db_folder_act.triggered.connect(self.on_choose_db_folder_triggered)

        self.folder_description_label = QLabel(self)
        self.folder_description_label.setTextFormat(Qt.MarkdownText)
        self.folder_description_label.setText(
            self.tr(
                """This is where cutevariant will look for annotation reference databases.
Every file in this folder with a .db extension must comply with the <a href='#annotation-reference-database-guidelines'>following guidelines</a>
"""
            )
        )
        self.folder_description_label.linkActivated.connect(open_link)

        self.db_list_view = QListView(self)
        self.db_model = AnnRefListModel(0, 0, self)
        self.db_list_view.setModel(self.db_model)

        self.button_add_database = QPushButton(self.tr("Add existing database"), self)
        self.button_add_database.clicked.connect(self.on_add_database_button_pressed)

        self.button_delete_database = QPushButton(
            self.tr("Delete selected database"), self
        )
        self.button_delete_database.clicked.connect(
            self.on_delete_database_button_pressed
        )

        self.button_create_database_from_file = QPushButton(
            self.tr("Create database from file"), self
        )
        self.button_create_database_from_file.clicked.connect(
            self.on_create_database_from_file_button_pressed
        )

        self.edit_buttons_boxlayout = QVBoxLayout()
        self.edit_buttons_boxlayout.addWidget(self.button_add_database)
        self.edit_buttons_boxlayout.addWidget(self.button_delete_database)
        self.edit_buttons_boxlayout.addWidget(self.button_create_database_from_file)
        self.edit_buttons_boxlayout.addItem(
            QSpacerItem(0, 100, QSizePolicy.Fixed, QSizePolicy.Expanding)
        )

        self.db_selection_layout = QHBoxLayout()
        self.db_selection_layout.addWidget(self.db_list_view)
        self.db_selection_layout.addLayout(self.edit_buttons_boxlayout)

        vboxlayout = QVBoxLayout(self)
        vboxlayout.addWidget(self.folder_description_label)
        vboxlayout.addWidget(self.line_edit_database_folder_path)
        vboxlayout.addLayout(self.db_selection_layout)

        vboxlayout.addItem(QSpacerItem(0, 10, QSizePolicy.Fixed, QSizePolicy.Expanding))

    def on_choose_db_folder_triggered(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            self.tr("Please choose a folder with annotation reference databases"),
            self._database_folder_path,
        )
        if folder:
            self._database_folder_path = folder
            self.db_model.load(self._database_folder_path)

    def on_add_database_button_pressed(self):
        pass

    def on_delete_database_button_pressed(self):
        pass

    def on_create_database_from_file_button_pressed(self):
        pass

    def save(self):
        """Override from PageWidget"""
        pass

    def load(self):
        """Override from PageWidget"""

        # Load view that lists all available annotation reference databases
        settings = self.create_settings()
        self._database_folder_path = settings.value(
            "database_folder_path", QDir.homePath()
        )
        self.line_edit_database_folder_path.setText(self._database_folder_path)
        self.db_model.load(self._database_folder_path)


class GeneViewerSettingsWidget(PluginSettingsWidget):
    """Instantiated plugin in the settings panel of Cutevariant

    Allows users to choose the annotation database used by the geneviewer.
    It is the responsibility of the user to have a database with gene name entries that match gene names from the VCF they are analyzing.
    """

    ENABLE = True

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowIcon(FIcon(0xF11CC))
        self.setWindowTitle("Gene viewer")
        self.add_page(AnnRefDatabaseSettings())


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    dlg = GuidelinesDialog()
    dlg.show()
    exit(app.exec_())
