import sys

from PyQt5 import QtGui, Qt
from PyQt5.QtCore import *
from PyQt5.QtGui import QIntValidator, QRegularExpressionValidator
from PyQt5.QtWidgets import QStackedWidget, QWidget, QTabWidget, QFrame, QGridLayout, QHBoxLayout, \
    QVBoxLayout, QListWidgetItem, QCheckBox, QListWidget, QLabel, QApplication, QComboBox, QLineEdit, \
    QTableWidget, QTableWidgetItem, QPushButton, QColorDialog, QHeaderView, QStyledItemDelegate
from ImgMesh.Qss.QssList import QSS2

reg1 = QRegularExpression("[0-9]+$")
validator1 = QRegularExpressionValidator()
validator1.setRegularExpression(reg1)

reg2 = QRegularExpression("^([0-9]|[1-9][0-9]|1[0-7][0-9]|180)(\.\d{1,2})?$")  # validator2 0-180 .00
validator2 = QRegularExpressionValidator()
validator2.setRegularExpression(reg2)


def enable_dynamic_row_addition(tableWidget):
    def add_empty_row():
        current_row_count = tableWidget.rowCount()
        tableWidget.insertRow(current_row_count)

        item = QTableWidgetItem()
        tableWidget.setItem(current_row_count, 1, item)
        tableWidget.editItem(item)

    def keyPressEvent(event):
        # 在按下回车键时新增一行
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            current_item = tableWidget.currentItem()
            if current_item is not None:
                current_row = current_item.row()
                current_col = current_item.column()
                if current_col == tableWidget.columnCount() - 1 and current_row == tableWidget.rowCount() - 1:
                    add_empty_row()

    tableWidget.installEventFilter(tableWidget)
    tableWidget.keyPressEvent = keyPressEvent


class RangeDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setValidator(QIntValidator(0, 255))
        return editor

    def setEditorData(self, editor, index):
        value = index.data(Qt.EditRole)
        editor.setText(str(value))

    def setModelData(self, editor, model, index):
        text = editor.text()
        model.setData(index, int(text) if text.isdigit() else 0, Qt.EditRole)


class COLOR_TRANSFER_FUNCTION_WIDGET(QWidget):
    def __init__(self):
        super().__init__()

        self.btns = []

        layout = QVBoxLayout()

        # Color table
        self.color_table = QTableWidget(2, 5)
        delegate = RangeDelegate()
        self.color_table.setItemDelegate(delegate)

        self.color_table.setHorizontalHeaderLabels(["Gray", "Color", "R", "G", "B"])
        self.color_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.color_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)

        self.color_table.setItem(0, 0, QTableWidgetItem(str(0)))
        self.color_table.setItem(0, 2, QTableWidgetItem(str(0)))
        self.color_table.setItem(0, 3, QTableWidgetItem(str(0)))
        self.color_table.setItem(0, 4, QTableWidgetItem(str(0)))

        self.color_table.setItem(1, 0, QTableWidgetItem(str(255)))
        self.color_table.setItem(1, 2, QTableWidgetItem(str(0)))
        self.color_table.setItem(1, 3, QTableWidgetItem(str(255)))
        self.color_table.setItem(1, 4, QTableWidgetItem(str(255)))

        self.btns.append(QPushButton())
        self.btns[0].setStyleSheet("background-color: rgb(0, 0,0);")
        self.color_table.setCellWidget(0, 1, self.btns[0])
        self.btns[0].clicked.connect(lambda: self.change_color(0))

        self.btns.append(QPushButton())
        self.btns[1].setStyleSheet(f"background-color: rgb(0,255.0,255.0)")
        self.color_table.setCellWidget(1, 1, self.btns[1])
        self.btns[1].clicked.connect(lambda: self.change_color(1))

        layout.addWidget(self.color_table)
        # enable_dynamic_row_addition(self.color_table)

        self.color_table.cellChanged.connect(self.change_image_color)

        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def change_image_color(self, row, col):
        if col > 1:
            if len(self.btns) < row + 1:
                self.btns.append(QPushButton())
                self.color_table.setCellWidget(row, 1, self.btns[row])

            temp = [self.color_table.item(row, 2), self.color_table.item(row, 3), self.color_table.item(row, 4)]
            for id, t in enumerate(temp):
                if t is None:
                    temp[id] = '0'
                else:
                    temp[id] = t.text()

            self.btns[row].setStyleSheet(f"background-color: rgb({int(temp[0])},"
                                         f" {int(temp[1])}, "
                                         f"{int(temp[2])})")


    def change_color(self, row):
        color = QColorDialog.getColor()

        if color.isValid():
            r, g, b, _ = color.getRgbF()

            self.color_table.setItem(row, 2, QTableWidgetItem(str(int(r * 255))))
            self.color_table.setItem(row, 3, QTableWidgetItem(str(int(g * 255))))
            self.color_table.setItem(row, 4, QTableWidgetItem(str(int(b * 255))))
            self.btns[row].setStyleSheet(f"background-color: rgb({int(r * 255)}, {int(g * 255)}, {int(b * 255)})")

    def add_color(self):
        row_position = self.color_table.rowCount()
        self.color_table.insertRow(row_position)

        color = QColorDialog.getColor()

        if color.isValid():
            r, g, b, _ = color.getRgbF()

            self.color_table.setItem(row_position, 2, QTableWidgetItem(str(r * 255)))
            self.color_table.setItem(row_position, 3, QTableWidgetItem(str(g * 255)))
            self.color_table.setItem(row_position, 4, QTableWidgetItem(str(b * 255)))

            self.btns.append(QPushButton())
            self.btns[row_position].setStyleSheet(
                f"background-color: rgb({int(r * 255)}, {int(g * 255)}, {int(b * 255)})")
            self.color_table.setCellWidget(row_position, 1, self.btns[row_position])
            self.btns[row_position].clicked.connect(lambda: self.change_color(row_position))


class Win_Setting(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Setting')
        self.setWindowIcon(QtGui.QIcon(":/icon/set.png"))
        self.setFixedSize(420, 520)
        self.main_layout = QHBoxLayout(self, spacing=0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(QSS2)
        self.stacked_widget = QStackedWidget()

        self.main_layout.addWidget(self.list_widget)
        self.main_layout.addWidget(self.stacked_widget)

        # create pages
        self.page_image = QWidget()
        self.page_image.setObjectName("Image page")
        self.stacked_widget.addWidget(self.page_image)

        self.page_pointcloud = QWidget()
        self.page_pointcloud.setObjectName("Point cloud page")
        self.stacked_widget.addWidget(self.page_pointcloud)

        self.page_mesh = QWidget()
        self.page_mesh.setObjectName("Mesh page")
        self.stacked_widget.addWidget(self.page_mesh)
        self.stacked_widget.setCurrentIndex(2)

        self.HLayout_2 = QHBoxLayout(self.page_mesh)
        self.HLayout_2.setContentsMargins(0, 0, 0, 0)

        self.tab_general = QWidget()
        self.VLayout_general = QVBoxLayout(self.tab_general)

        # mesh generation
        reg1 = QRegularExpression('(/^[01]$|^0.\d{2}/)|1')  # validator1 0-1 .00
        validator1 = QRegularExpressionValidator()
        validator1.setRegularExpression(reg1)
        self.frame_mesh = QFrame(self.tab_general)
        self.frame_mesh.setFrameShape(QFrame.Box)
        self.frame_mesh.setFrameShadow(QFrame.Raised)
        self.frame_mesh.setLineWidth(1)
        self.GLayout_mesh = QGridLayout(self.frame_mesh)

        self.checkbox_2dmesh = QCheckBox(self.frame_mesh)
        self.checkbox_2dmesh.setText('2D Mesh Generation')
        self.checkbox_2dmesh.setFont(QtGui.QFont('微软雅黑', 10, weight=QtGui.QFont.Bold))
        self.checkbox_2dmesh.setChecked(True)

        self.label_2d_mesh_gen_algorithm = QLabel(self.frame_mesh)
        self.label_2d_mesh_gen_algorithm.setText("Algorithm")
        self.label_2d_mesh_gen_algorithm.setFont(QtGui.QFont('微软雅黑', 10))

        self.combobox_2d_mesh_gen = QComboBox()
        self.combobox_2d_mesh_gen.addItem("Greedy-Crust")
        self.combobox_2d_mesh_gen.addItem("Matching Cubes")
        self.combobox_2d_mesh_gen.addItem("Open3d_Alpha shapes")
        self.combobox_2d_mesh_gen.addItem("Open3d_Poisson")
        self.combobox_2d_mesh_gen.addItem("Open3d_Ball pivoting")
        self.combobox_2d_mesh_gen.setFont(QtGui.QFont('微软雅黑', 10))

        self.combobox_2d_mesh_gen.currentIndexChanged.connect(self.show_selected_table)

        self.checkbox_quadmesh = QCheckBox(self.frame_mesh)
        self.checkbox_quadmesh.setText('Quad Mesh')
        self.checkbox_quadmesh.setFont(QtGui.QFont('微软雅黑', 10))
        self.checkbox_quadmesh.setChecked(True)

        self.checkbox_openmesh = QCheckBox(self.frame_mesh)
        self.checkbox_openmesh.setText('Open Mesh')
        self.checkbox_openmesh.setFont(QtGui.QFont('微软雅黑', 10))
        self.checkbox_openmesh.setChecked(False)

        self.checkbox_backgroundmesh = QCheckBox(self.frame_mesh)
        self.checkbox_backgroundmesh.setText('Background Mesh')
        self.checkbox_backgroundmesh.setFont(QtGui.QFont('微软雅黑', 10))
        self.checkbox_backgroundmesh.setChecked(False)

        self.table_greedy_crust = QTableWidget(1, 5)
        self.table_greedy_crust.setHorizontalHeaderLabels(["Offset", 'N', "IF", "Sliver(°)", "Flat(°)"])
        self.table_greedy_crust.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_greedy_crust.setFont(QtGui.QFont('微软雅黑', 10))
        self.table_greedy_crust.setItem(0, 0, QTableWidgetItem(str(1)))
        self.table_greedy_crust.setItem(0, 1, QTableWidgetItem(str(20)))
        self.table_greedy_crust.setItem(0, 2, QTableWidgetItem(str(-0.8)))
        self.table_greedy_crust.setItem(0, 3, QTableWidgetItem(str(120)))
        self.table_greedy_crust.setItem(0, 4, QTableWidgetItem(str(0)))

        self.table_greedy_crust.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.table_matching_cubes = QTableWidget(1, 2)
        self.table_matching_cubes.setHorizontalHeaderLabels(["Number", "Value"])
        self.table_matching_cubes.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_matching_cubes.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_matching_cubes.setItem(0, 0, QTableWidgetItem(str(0)))
        self.table_matching_cubes.setItem(0, 1, QTableWidgetItem(str(255)))
        self.table_matching_cubes.setFont(QtGui.QFont('微软雅黑', 10))
        enable_dynamic_row_addition(self.table_matching_cubes)
        self.table_matching_cubes.hide()

        self.table_o3d_alpha = QTableWidget(1, 1)
        self.table_o3d_alpha.setHorizontalHeaderLabels(["Alpha"])
        self.table_o3d_alpha.setFont(QtGui.QFont('微软雅黑', 10))
        self.table_o3d_alpha.setItem(0, 0, QTableWidgetItem(str(0.1)))
        self.table_o3d_alpha.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.table_crust.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_o3d_alpha.hide()

        self.table_o3d_poisson = QTableWidget(1, 2)
        self.table_o3d_poisson.setHorizontalHeaderLabels(["Depth", "Max_nn"])
        self.table_o3d_poisson.setFont(QtGui.QFont('微软雅黑', 10))
        self.table_o3d_poisson.setItem(0, 0, QTableWidgetItem(str(8)))
        self.table_o3d_poisson.setItem(0, 1, QTableWidgetItem(str(30)))
        self.table_o3d_poisson.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.table_crust.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_o3d_poisson.hide()

        self.table_o3d_ball_pivoting = QTableWidget(1, 2)
        self.table_o3d_ball_pivoting.setHorizontalHeaderLabels(["Radii", "Max_nn"])
        self.table_o3d_ball_pivoting.setFont(QtGui.QFont('微软雅黑', 10))
        self.table_o3d_ball_pivoting.setItem(0, 0, QTableWidgetItem("0.01,0.02"))
        self.table_o3d_ball_pivoting.setItem(0, 1, QTableWidgetItem(str(30)))
        self.table_o3d_ball_pivoting.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.table_crust.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_o3d_ball_pivoting.hide()

        self.frame_mesh_table = QFrame(self.frame_mesh)

        self.VLayout_mesh_table = QGridLayout(self.frame_mesh_table)
        self.VLayout_mesh_table.addWidget(self.table_greedy_crust)
        self.VLayout_mesh_table.addWidget(self.table_matching_cubes)
        self.VLayout_mesh_table.addWidget(self.table_o3d_alpha)
        self.VLayout_mesh_table.addWidget(self.table_o3d_poisson)
        self.VLayout_mesh_table.addWidget(self.table_o3d_ball_pivoting)

        self.VLayout_mesh_table.setContentsMargins(0, 0, 0, 0)

        self.GLayout_mesh.addWidget(self.checkbox_2dmesh, 0, 0, 1, 3)
        self.GLayout_mesh.addWidget(self.checkbox_quadmesh, 1, 0, 1, 3)
        self.GLayout_mesh.addWidget(self.checkbox_openmesh, 1, 2, 1, 1)
        self.GLayout_mesh.addWidget(self.checkbox_backgroundmesh, 2, 0, 1, 3)

        self.GLayout_mesh.addWidget(self.label_2d_mesh_gen_algorithm, 3, 0, 1, 1)
        self.GLayout_mesh.addWidget(self.combobox_2d_mesh_gen, 3, 2, 1, 2)
        self.GLayout_mesh.addWidget(self.frame_mesh_table, 4, 0, 2, 4)
        self.GLayout_mesh.setContentsMargins(5, 0, 5, 0)

        # mesh smooth
        self.frame_smooth = QFrame(self.tab_general)
        self.frame_smooth.setFrameShape(QFrame.Box)
        self.frame_smooth.setFrameShadow(QFrame.Raised)
        self.frame_smooth.setLineWidth(1)

        self.checkbox_smooth = QCheckBox(self.frame_smooth)
        self.checkbox_smooth.setText('Mesh smooth')
        self.checkbox_smooth.setChecked(True)
        self.checkbox_smooth.setFont(QtGui.QFont('微软雅黑', 10, weight=QtGui.QFont.Bold))

        self.label_smoothalgorithm = QLabel(self.frame_smooth)
        self.label_smoothalgorithm.setText('Algorithm')
        self.label_smoothalgorithm.setFont(QtGui.QFont('微软雅黑', 10))

        self.combobox_smoothalgorithm = QComboBox(self.frame_smooth)
        self.combobox_smoothalgorithm.addItem("vtkWindowedSincPolyDataFilter")
        self.combobox_smoothalgorithm.addItem("vtkSmoothPolyDataFilter")

        self.checkBox_boundsmooth = QCheckBox(self.frame_smooth)
        self.checkBox_boundsmooth.setText("Boundary smooth")
        self.checkBox_boundsmooth.setFont(QtGui.QFont('微软雅黑', 10))

        self.checkBox_featureedgesmooth = QCheckBox(self.frame_smooth)
        self.checkBox_featureedgesmooth.setText("Feature smooth")
        self.checkBox_featureedgesmooth.setFont(QtGui.QFont('微软雅黑', 10))

        self.label_iterations = QLabel(self.frame_smooth)
        self.label_iterations.setText("Iterations")
        self.label_iterations.setFont(QtGui.QFont('微软雅黑', 10))

        self.lineedit_iterations = QLineEdit('10')
        self.lineedit_iterations.setValidator(QIntValidator(0, 999999))
        self.lineedit_iterations.setFont(QtGui.QFont('Times New Roman', 10))
        self.lineedit_iterations.setAlignment(Qt.AlignCenter)

        self.label_featureangle = QLabel(self.frame_smooth)
        self.label_featureangle.setText("Feature angle")
        self.label_featureangle.setFont(QtGui.QFont('微软雅黑', 10))

        self.lineedit_featureangle = QLineEdit('45')
        self.lineedit_featureangle.setValidator(validator2)
        self.lineedit_featureangle.setMaximumWidth(40)
        self.lineedit_featureangle.setFont(QtGui.QFont('Times New Roman', 10))
        self.lineedit_featureangle.setAlignment(Qt.AlignCenter)

        self.GLayout_smooth = QGridLayout(self.frame_smooth)
        self.GLayout_smooth.addWidget(self.checkbox_smooth, 0, 0, 1, 10)
        self.GLayout_smooth.addWidget(self.label_smoothalgorithm, 1, 0, 1, 2)
        self.GLayout_smooth.addWidget(self.combobox_smoothalgorithm, 1, 2, 1, 9)
        self.GLayout_smooth.addWidget(self.checkBox_boundsmooth, 2, 0, 1, 5)
        self.GLayout_smooth.addWidget(self.checkBox_featureedgesmooth, 2, 6, 1, 5)
        self.GLayout_smooth.addWidget(self.label_iterations, 3, 0, 1, 2)
        self.GLayout_smooth.addWidget(self.lineedit_iterations, 3, 2, 1, 2)
        self.GLayout_smooth.addWidget(self.label_featureangle, 3, 5, 1, 4)
        self.GLayout_smooth.addWidget(self.lineedit_featureangle, 3, 9, 1, 1)

        self.GLayout_smooth.setContentsMargins(5, 0, 5, 0)

        # 3D mesh generation
        self.frame_3dmesh = QFrame(self.tab_general)
        self.frame_3dmesh.setFrameShape(QFrame.Box)
        self.frame_3dmesh.setFrameShadow(QFrame.Raised)
        self.frame_3dmesh.setLineWidth(1)

        self.checkbox_3dmesh = QCheckBox(self.frame_3dmesh)
        self.checkbox_3dmesh.setText('3D Mesh generation')
        self.checkbox_3dmesh.setChecked(True)
        self.checkbox_3dmesh.setFont(QtGui.QFont('微软雅黑', 10, weight=QtGui.QFont.Bold))

        self.label_3dmeshalgorithm = QLabel(self.frame_3dmesh)
        self.label_3dmeshalgorithm.setText("Algorithm")
        self.label_3dmeshalgorithm.setFont(QtGui.QFont('微软雅黑', 10))

        self.combobox_3dmeshalgorithm = QComboBox(self.frame_3dmesh)
        self.combobox_3dmeshalgorithm.addItems(['Delaunay', 'Initial mesh only', 'Frontal', 'MMG3D', 'R-tree', 'HXT'])

        self.label_minmaxsize = QLabel(self.frame_3dmesh)
        self.label_minmaxsize.setText("Min/max mesh size")
        self.label_minmaxsize.setFont(QtGui.QFont('微软雅黑', 10))

        self.lineedit_minsize = QLineEdit('0')
        self.lineedit_minsize.setValidator(QIntValidator(0, 1e6))
        self.lineedit_minsize.setMaximumWidth(40)
        self.lineedit_minsize.setFont(QtGui.QFont('Times New Roman', 10))
        self.lineedit_minsize.setAlignment(Qt.AlignCenter)

        self.label_to = QLabel(self.frame_3dmesh)
        self.label_to.setText("-")
        self.label_to.setFont(QtGui.QFont('微软雅黑', 10))

        self.lineedit_maxsize = QLineEdit('1e16')
        self.lineedit_maxsize.setValidator(QIntValidator(0, 1e6))
        self.lineedit_maxsize.setMaximumWidth(40)
        self.lineedit_maxsize.setFont(QtGui.QFont('Times New Roman', 10))
        self.lineedit_maxsize.setAlignment(Qt.AlignCenter)

        self.GLayout_3dmesh = QGridLayout(self.frame_3dmesh)
        self.GLayout_3dmesh.addWidget(self.checkbox_3dmesh, 0, 0, 1, 10)
        self.GLayout_3dmesh.addWidget(self.label_3dmeshalgorithm, 1, 0, 1, 2)
        self.GLayout_3dmesh.addWidget(self.combobox_3dmeshalgorithm, 1, 3, 1, 8)
        self.GLayout_3dmesh.addWidget(self.label_minmaxsize, 2, 0, 1, 5)
        self.GLayout_3dmesh.addWidget(self.lineedit_minsize, 2, 6, 1, 2)
        self.GLayout_3dmesh.addWidget(self.label_to, 2, 8, 1, 1)
        self.GLayout_3dmesh.addWidget(self.lineedit_maxsize, 2, 9, 1, 2)
        self.GLayout_3dmesh.setContentsMargins(5, 0, 5, 0)

        self.VLayout_general.addWidget(self.frame_mesh)
        self.VLayout_general.addWidget(self.frame_smooth)
        self.VLayout_general.addWidget(self.frame_3dmesh)
        # self.VLayout_general.setContentsMargins(10, 10, 10, 50)

        self.tabWidget2 = QTabWidget(self.page_mesh)
        self.tabWidget2.setTabText(0, "Display")
        self.tabWidget2.setStyleSheet('QTabBar { font-size: 10pt; font-family: 微软雅黑; }')

        self.tab_mesh_show = QWidget()
        self.VLayout_show = QVBoxLayout(self.tab_mesh_show)
        self.frame_2dsetting = QFrame(self.tab_mesh_show)
        self.frame_2dsetting.setFrameShape(QFrame.Box)
        self.frame_2dsetting.setFrameShadow(QFrame.Raised)
        self.frame_2dsetting.setLineWidth(1)
        self.checkBox_2dnode = QCheckBox(self.frame_2dsetting)
        self.checkBox_2dnode.setText("2D nodes label")
        self.checkBox_2dnode.setFont(QtGui.QFont('微软雅黑', 10))
        self.checkBox_2delement = QCheckBox(self.frame_2dsetting)
        self.checkBox_2delement.setText("2D element label")
        self.checkBox_2delement.setFont(QtGui.QFont('微软雅黑', 10))
        self.checkBox_2dbound = QCheckBox(self.frame_2dsetting)
        self.checkBox_2dbound.setText("2D boundaries")
        self.checkBox_2dbound.setFont(QtGui.QFont('微软雅黑', 10))
        self.checkBox_2dcheck = QCheckBox(self.frame_2dsetting)
        self.checkBox_2dcheck.setText("2D mesh check")
        self.checkBox_2dcheck.setFont(QtGui.QFont('微软雅黑', 10))

        self.checkBox_2dframe = QCheckBox(self.frame_2dsetting)
        self.checkBox_2dframe.setText("2D element edge")
        self.checkBox_2dframe.setFont(QtGui.QFont('微软雅黑', 10))
        self.checkBox_2dframe.setChecked(1)
        self.checkBox_2dface = QCheckBox(self.frame_2dsetting)
        self.checkBox_2dface.setText("2D element face")
        self.checkBox_2dface.setFont(QtGui.QFont('微软雅黑', 10))
        self.checkBox_2dface.setChecked(1)
        self.VLayout_show.addWidget(self.frame_2dsetting)

        self.GLayout = QGridLayout(self.frame_2dsetting)
        self.GLayout.addWidget(self.checkBox_2dnode, 0, 0, 1, 1)
        self.GLayout.addWidget(self.checkBox_2delement, 0, 1, 1, 1)
        self.GLayout.addWidget(self.checkBox_2dbound, 1, 0, 1, 1)
        self.GLayout.addWidget(self.checkBox_2dcheck, 1, 1, 1, 1)
        self.GLayout.addWidget(self.checkBox_2dframe, 2, 0, 1, 1)
        self.GLayout.addWidget(self.checkBox_2dface, 2, 1, 1, 1)

        self.VLayout_show.setContentsMargins(10, 10, 10, 380)

        self.tabWidget2.addTab(self.tab_general, 'General')
        self.tabWidget2.addTab(self.tab_mesh_show, 'Display')

        self.HLayout_2.addWidget(self.tabWidget2)

        # Image
        self.tab_image = QTabWidget(self.page_image)
        self.tab_image.setTabText(0, "General")
        self.tab_image.setStyleSheet('QTabBar { font-size: 10pt; font-family: 微软雅黑; }')
        self.tab_image.setTabText(1, "Display")
        self.tab_image.setStyleSheet('QTabBar { font-size: 10pt; font-family: 微软雅黑; }')

        self.tab_image_general = QWidget()
        self.VLayout_image_general = QVBoxLayout(self.tab_image_general)
        self.frame_image_general = QFrame(self.tab_image_general)
        self.frame_image_general.setFrameShape(QFrame.Box)
        self.frame_image_general.setFrameShadow(QFrame.Raised)
        self.frame_image_general.setLineWidth(1)
        self.VLayout_image_general.addWidget(self.frame_image_general)

        self.tab_image_show = QWidget()
        self.VLayout_image_show = QVBoxLayout(self.tab_image_show)
        self.frame_image_show = QFrame(self.tab_image_show)
        self.frame_image_show.setFrameShape(QFrame.Box)
        self.frame_image_show.setFrameShadow(QFrame.Raised)
        self.frame_image_show.setLineWidth(1)
        self.VLayout_image_show.addWidget(self.frame_image_show)

        self.tab_image.addTab(self.tab_image_general, 'General')
        self.tab_image.addTab(self.tab_image_show, 'Display')

        self.VLayout_image_general.setContentsMargins(10, 10, 10, 350)
        self.VLayout_image_show.setContentsMargins(10, 10, 10, 250)

        self.HLayout_image = QHBoxLayout(self.page_image)
        self.HLayout_image.setContentsMargins(0, 0, 0, 0)
        self.HLayout_image.addWidget(self.tab_image)

        self.checkBox_bounding_box = QCheckBox(self.frame_image_show)
        self.checkBox_bounding_box.setText("Bounding box")
        self.checkBox_bounding_box.setFont(QtGui.QFont('微软雅黑', 10))
        self.checkBox_bounding_box.setChecked(0)

        self.GLayout_image_show = QGridLayout(self.frame_image_show)
        self.GLayout_image_show.addWidget(self.checkBox_bounding_box, 0, 0, 1, 1)
        self.GLayout_image_show.setContentsMargins(10, 10, 10, 20)

        self.checkBox_imagesmooth = QCheckBox(self.frame_image_general)
        self.checkBox_imagesmooth.setText("ImageGaussianSmooth")
        self.checkBox_imagesmooth.setFont(QtGui.QFont('微软雅黑', 10))
        self.checkBox_imagesmooth.setChecked(1)

        self.GLayout_image_general = QGridLayout(self.frame_image_general)
        self.GLayout_image_general.addWidget(self.checkBox_imagesmooth, 0, 0, 1, 4)
        self.GLayout_image_general.setContentsMargins(10, 10, 10, 20)

        self.label_image_Gaussian_Dimensionality = QLabel("Dimensionality", self)
        self.label_image_Gaussian_Dimensionality.setFont(QtGui.QFont('微软雅黑', 10))
        self.GLayout_image_general.addWidget(self.label_image_Gaussian_Dimensionality, 1, 0, 1, 1)
        self.lineedit_image_Gaussian_Dimensionality = QLineEdit("3", self)
        self.lineedit_image_Gaussian_Dimensionality.setFont(QtGui.QFont('微软雅黑', 10))
        self.GLayout_image_general.addWidget(self.lineedit_image_Gaussian_Dimensionality, 1, 1, 1, 1)

        self.label_image_RadiusFactor= QLabel("RadiusFactor", self)
        self.label_image_RadiusFactor.setFont(QtGui.QFont('微软雅黑', 10))
        self.GLayout_image_general.addWidget(self.label_image_RadiusFactor, 2, 0, 1, 1)
        self.lineedit_image_RadiusFactor1 = QLineEdit("5", self)
        self.lineedit_image_RadiusFactor1.setFont(QtGui.QFont('微软雅黑', 10))
        self.GLayout_image_general.addWidget(self.lineedit_image_RadiusFactor1, 2, 1, 1, 1)
        self.lineedit_image_RadiusFactor2 = QLineEdit("5", self)
        self.lineedit_image_RadiusFactor2.setFont(QtGui.QFont('微软雅黑', 10))
        self.GLayout_image_general.addWidget(self.lineedit_image_RadiusFactor2, 2, 2, 1, 1)
        self.lineedit_image_RadiusFactor3 = QLineEdit("5", self)
        self.lineedit_image_RadiusFactor3.setFont(QtGui.QFont('微软雅黑', 10))
        self.GLayout_image_general.addWidget(self.lineedit_image_RadiusFactor3, 2, 3, 1, 1)


        self.label_image_StandardDeviation= QLabel("StandardDeviation", self)
        self.label_image_StandardDeviation.setFont(QtGui.QFont('微软雅黑', 10))
        self.GLayout_image_general.addWidget(self.label_image_StandardDeviation, 3, 0, 1, 1)
        self.lineedit_image_StandardDeviation1 = QLineEdit("3", self)
        self.lineedit_image_StandardDeviation1.setFont(QtGui.QFont('微软雅黑', 10))
        self.GLayout_image_general.addWidget(self.lineedit_image_StandardDeviation1, 3, 1, 1, 1)
        self.lineedit_image_StandardDeviation2 = QLineEdit("3", self)
        self.lineedit_image_StandardDeviation2.setFont(QtGui.QFont('微软雅黑', 10))
        self.GLayout_image_general.addWidget(self.lineedit_image_StandardDeviation2, 3, 2, 1, 1)
        self.lineedit_image_StandardDeviation3 = QLineEdit("3", self)
        self.lineedit_image_StandardDeviation3.setFont(QtGui.QFont('微软雅黑', 10))
        self.GLayout_image_general.addWidget(self.lineedit_image_StandardDeviation3, 3,3, 1, 1)


        self.color_trans_table = COLOR_TRANSFER_FUNCTION_WIDGET()
        self.VLayout_image_show.addWidget(self.color_trans_table)


        # Point cloud

        self.tab_pointcloud = QTabWidget(self.page_pointcloud)
        self.tab_pointcloud.setStyleSheet('QTabBar { font-size: 10pt; font-family: 微软雅黑; }')

        self.HLayout_pointcloud = QHBoxLayout(self.page_pointcloud)
        self.HLayout_pointcloud.setContentsMargins(0, 0, 0, 0)
        self.HLayout_pointcloud.addWidget(self.tab_pointcloud)

        self.tab_pointcloud_general = QWidget()
        self.VLayout_pointcloud_general = QVBoxLayout(self.tab_pointcloud_general)
        self.frame_pointcloud_general = QFrame(self.tab_pointcloud_general)
        self.frame_pointcloud_general.setFrameShape(QFrame.Box)
        self.frame_pointcloud_general.setFrameShadow(QFrame.Raised)
        self.frame_pointcloud_general.setLineWidth(1)
        self.tab_pointcloud.addTab(self.tab_pointcloud_general, 'General')
        self.VLayout_pointcloud_general.addWidget(self.frame_pointcloud_general)
        self.VLayout_pointcloud_general.setContentsMargins(10, 10, 10, 400)

        self.GLayout_pointcloud_general = QGridLayout(self.frame_pointcloud_general)
        self.label_PC_downsample = QLabel("Downsampling algorithm", self)
        self.label_PC_downsample.setFont(QtGui.QFont('微软雅黑', 10))

        self.GLayout_pointcloud_general.setContentsMargins(10, 10, 10, 20)

        self.combobox_downsample = QComboBox()
        self.combobox_downsample.addItem("Voxel_down_sample")
        self.combobox_downsample.addItem("Uniform_down_sample")
        self.combobox_downsample.addItem("Random_down_sample")
        self.combobox_downsample.setFont(QtGui.QFont('微软雅黑', 10))

        self.lineedit_downsample = QLineEdit()
        self.lineedit_downsample.setText("1")

        self.GLayout_pointcloud_general.addWidget(self.label_PC_downsample, 0, 0, 1, 2)
        self.GLayout_pointcloud_general.addWidget(self.lineedit_downsample, 0, 3, 1, 1)
        self.GLayout_pointcloud_general.addWidget(self.combobox_downsample, 1, 0, 1, 4)

        self.tab_pointcloud_show = QWidget()
        self.VLayout_pointcloud_show = QVBoxLayout(self.tab_pointcloud_show)
        self.frame_pointcloud_show = QFrame(self.tab_pointcloud_show)
        self.frame_pointcloud_show.setFrameShape(QFrame.Box)
        self.frame_pointcloud_show.setFrameShadow(QFrame.Raised)
        self.frame_pointcloud_show.setLineWidth(1)
        self.tab_pointcloud.addTab(self.tab_pointcloud_show, 'Display')

        self.VLayout_pointcloud_show.addWidget(self.frame_pointcloud_show)
        self.VLayout_pointcloud_show.setContentsMargins(10, 10, 10, 400)

        self.label_PC_color = QLabel("Points color", self)
        self.label_PC_color.setFont(QtGui.QFont('微软雅黑', 10))

        self.btn_PC_color = QPushButton(self.frame_pointcloud_show)
        self.btn_PC_color.setStyleSheet("background-color: rgb(0,0,255);")
        self.btn_PC_color.clicked.connect(self.change_PC_color)

        self.lineedit1_Pc_color = QLineEdit()
        self.lineedit2_Pc_color = QLineEdit()
        self.lineedit3_Pc_color = QLineEdit()

        # 设置数字输入框的范围
        self.lineedit1_Pc_color.setText("0")
        self.lineedit2_Pc_color.setText("0")
        self.lineedit3_Pc_color.setText("255")
        self.lineedit1_Pc_color.textChanged.connect(self.validate_input)
        self.lineedit2_Pc_color.textChanged.connect(self.validate_input)
        self.lineedit3_Pc_color.textChanged.connect(self.validate_input)

        self.label_PC_size = QLabel("Points size", self)
        self.label_PC_size.setFont(QtGui.QFont('微软雅黑', 10))

        self.lineedit_Pc_size = QLineEdit()
        self.lineedit_Pc_size.setText("4")

        self.GLayout_pointcloud_show = QGridLayout(self.frame_pointcloud_show)
        self.GLayout_pointcloud_show.setContentsMargins(10, 10, 10, 20)
        self.GLayout_pointcloud_show.addWidget(self.label_PC_size, 0, 0, 1, 1)
        self.GLayout_pointcloud_show.addWidget(self.lineedit_Pc_size, 0, 1, 1, 1)

        self.GLayout_pointcloud_show.addWidget(self.label_PC_color, 1, 0, 1, 1)
        self.GLayout_pointcloud_show.addWidget(self.btn_PC_color, 1, 1, 1, 1)
        self.GLayout_pointcloud_show.addWidget(self.lineedit1_Pc_color, 1, 2, 1, 1)
        self.GLayout_pointcloud_show.addWidget(self.lineedit2_Pc_color, 1, 3, 1, 1)
        self.GLayout_pointcloud_show.addWidget(self.lineedit3_Pc_color, 1, 4, 1, 1)

        self._setup_ui()

    def show_selected_table(self, index):
        tables = [
            self.table_greedy_crust,
            self.table_matching_cubes,
            self.table_o3d_alpha,
            self.table_o3d_poisson,
            self.table_o3d_ball_pivoting
        ]

        for table in tables:
            table.setHidden(True)

        # 根据 index 显示选定的表格
        selected_table = tables[index]
        selected_table.setHidden(False)

    def validate_input(self):
        sender = self.sender()
        text = sender.text()
        try:
            value = int(text)
            if value < 0:
                sender.setText("0")
            elif value > 255:
                sender.setText("255")
            else:
                self.btn_PC_color.setStyleSheet(f"background-color: rgb({int(self.lineedit1_Pc_color.text())},"
                                                f" {int(self.lineedit2_Pc_color.text())}, "
                                                f"{int(self.lineedit3_Pc_color.text())})")
        except ValueError:
            sender.setText("0")

    def _setup_ui(self):
        '''加载界面ui'''
        self.list_widget.setFrameShape(QListWidget.NoFrame)  # 去掉边框
        self.list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list_widget.itemClicked.connect(self.item_clicked)

        list_str = ['Image', 'Point', 'Mesh']
        for i in range(0, len(list_str)):
            self.item = QListWidgetItem(list_str[i], self.list_widget)  # 左侧选项的添加
            self.item.setSizeHint(QSize(30, 30))
            self.item.setFont(QtGui.QFont('微软雅黑', 10, QtGui.QFont.Bold))
            self.item.setTextAlignment(Qt.AlignCenter)  # 居中显示
        self.list_widget.setCurrentRow(2)

    def change_PC_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            r, g, b, _ = color.getRgbF()
            self.lineedit1_Pc_color.setText(str(int(r * 255)))
            self.lineedit2_Pc_color.setText(str(int(g * 255)))
            self.lineedit3_Pc_color.setText(str(int(b * 255)))
            self.btn_PC_color.setStyleSheet(f"background-color: rgb({int(r * 255)}, {int(g * 255)}, {int(b * 255)})")

    def item_clicked(self):
        # 获取当前选中的item
        item = self.list_widget.selectedItems()[0]
        if item.text() == 'Image':
            self.stacked_widget.setCurrentIndex(0)
        elif item.text() == 'Point':
            self.stacked_widget.setCurrentIndex(1)
        elif item.text() == 'Mesh':
            self.stacked_widget.setCurrentIndex(2)

    def checkbox_lineedit(self, btn, btn_le, text):
        if btn.isChecked():
            btn_le.setEnabled(True)
            btn_le.setText(text)
            btn_le.setStyleSheet("QLineEdit""{""background : rgb(255, 255, 255);""}")
        else:
            btn_le.setEnabled(False)
            btn_le.setText('')
            btn_le.setStyleSheet("QLineEdit""{""background : rgb(177, 206, 237);""}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    MainWindow = Win_Setting()
    MainWindow.show()
    sys.exit(app.exec_())
