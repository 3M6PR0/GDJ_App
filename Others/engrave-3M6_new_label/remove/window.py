from PyQt5.QtCore import Qt, QModelIndex
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import *


class TreeRow:
    def __init__(self, values=None):
        self.values = ["X"] * 6 if not values else values
        assert len(self.values) == 6
        self.children = []
        self.combobox_columns = {}

    def add(self, child: "TreeRow"):
        self.children.append(child)

    def remove(self, child: "TreeRow"):
        self.children.remove(child)

    def set_combobox(self, col_index: int, values: list[str]):
        self.combobox_columns[col_index] = values

    def create(self):
        items = [QStandardItem(x) for x in self.values]
        for col, combo_values in self.combobox_columns.items():
            combo_item = QStandardItem("")
            combo_item.setData(combo_values, Qt.UserRole)
            items[col] = combo_item
        for child in self.children:
            items[0].appendRow(child.create())
        return items


class JQEWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt5 App with TreeView")
        self.resize(1400, 800)
        # Central Widget and Split Layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.split_layout = QHBoxLayout(self.central_widget)

        # Left Frame (Scrollable area)
        self.left_frame = QFrame()
        self.left_layout = QVBoxLayout(self.left_frame)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.left_layout.addWidget(self.scroll_area)
        self.scroll_content = QWidget()
        self.scroll_area.setWidget(self.scroll_content)
        self.grid_layout = QGridLayout(self.scroll_content)
        self.split_layout.addWidget(self.left_frame)
        self.row = 0

        # Right Frame (Tree View)
        self.right_frame = QFrame()
        self.right_layout = QVBoxLayout(self.right_frame)
        self.split_layout.addWidget(self.right_frame)
        self.tree_view = QTreeView()
        self.tree_view.setEditTriggers(QTreeView.NoEditTriggers)  # Prevent editing
        self.tree_view.setIndentation(20)  # Set indentation for tree structure
        self.right_layout.addWidget(self.tree_view)

        # TreeView setup
        self.tree_model = QStandardItemModel()
        self.tree_model.setHorizontalHeaderLabels(["Item", "Qty", "Description", "Price", "Total", "Other"])
        self.tree_view.setModel(self.tree_model)
        self.tree_view.setColumnWidth(0, 250)
        self.tree_view.setColumnWidth(1, 50)
        self.tree_view.setColumnWidth(2, 400)

        # Buttons layout
        self.buttons_layout = QHBoxLayout()
        self.add_button = QPushButton("Add")
        self.remove_button = QPushButton("Remove")
        self.buttons_layout.addWidget(self.add_button)
        self.buttons_layout.addWidget(self.remove_button)

        # Add buttons layout to the main layout
        self.layout.addLayout(self.buttons_layout)

        # Connect button callbacks
        self.add_button.clicked.connect(self.on_add_button_clicked)
        self.remove_button.clicked.connect(self.on_remove_button_clicked)

    # Placeholder callback methods
    def on_add_button_clicked(self):
        print("Add button clicked")

    def on_remove_button_clicked(self):
        print("Remove button clicked")

    def set_tree(self, val: TreeRow):
        self.tree_model.appendRow(val.create())
        self.add_combobox_widgets(val)
        self.tree_view.expandAll()

    def add_combobox_widgets(self, tree_row: TreeRow, parent_index=QModelIndex()):
        parent_index = parent_index or QModelIndex()
        for row in range(self.tree_model.rowCount(parent_index)):
            index = self.tree_model.index(row, 0, parent_index)
            for col, combo_values in tree_row.combobox_columns.items():
                child_index = index.siblingAtColumn(col)
                if combo_values:
                    self.add_combobox_to_cell(child_index, combo_values)
            for child in tree_row.children:
                self.add_combobox_widgets(child, index)

    def add_combobox_to_cell(self, index, combo_values):
        combo = QComboBox(self.tree_view)
        combo.addItems(combo_values)
        self.tree_view.setIndexWidget(index, combo)

    def add_entry(self, text: str, entry_default: str = ""):
        label = QLabel(text)
        entry = QLineEdit()
        entry.setText(entry_default)

        self.grid_layout.addWidget(label, self.row, 0, alignment=Qt.AlignTop)
        self.grid_layout.addWidget(entry, self.row, 1)
        self.row += 1
        return entry

    def add_section(self, text: str):
        label = QLabel(f"<b>{text}</b>")
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)

        self.grid_layout.addWidget(label, self.row, 0, 1, 2)
        self.row += 1
        self.grid_layout.addWidget(line, self.row, 0, 1, 2)
        self.row += 1

    def add_combo(self, text: str, values: list[str]):
        label = QLabel(text)
        combo = QComboBox()
        combo.addItems(values)

        self.grid_layout.addWidget(label, self.row, 0, alignment=Qt.AlignTop)
        self.grid_layout.addWidget(combo, self.row, 1)
        self.row += 1
        return combo

    def add_button(self, text: str, callback):
        button = QPushButton(text)
        button.clicked.connect(callback)
        self.grid_layout.addWidget(button, self.row, 0, 1, 2, alignment=Qt.AlignCenter)
        self.row += 1