from PyQt5 import QtGui, Qt
from PyQt5.QtCore import *
import sys
from PyQt5.QtWidgets import QStackedWidget, QWidget, QFrame, QHBoxLayout, \
    QVBoxLayout, QListWidgetItem, QListWidget, QApplication, QPushButton
from ImgMesh.Qss.QssList import QSS2


class Win_mesh_edit(QWidget):
    dialogSignal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Mesh edit')
        self.setWindowIcon(QtGui.QIcon(":/icon/edit.png"))
        self.setFixedSize(250, 300)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        self.setFont(font)
        self.main_layout = QHBoxLayout(self, spacing=0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.listWidget = QListWidget()
        self.listWidget.setObjectName("listWidget")
        self.listWidget.setStyleSheet(QSS2)
        self.listWidget.setFrameShape(QListWidget.NoFrame)
        self.listWidget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.listWidget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.main_layout.addWidget(self.listWidget)

        self.item2 = QListWidgetItem('Elements', self.listWidget)
        self.item2.setSizeHint(QSize(30, 30))
        self.item2.setTextAlignment(Qt.AlignCenter)

        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)

        self.page2 = QWidget()
        self.page2.setObjectName("Element edit")
        self.stacked_widget.addWidget(self.page2)
        self.listWidget.setCurrentItem(self.item2)
        self.stacked_widget.setCurrentIndex(1)

        self.HLayout2 = QHBoxLayout(self.page2)

        self.frame2 = QFrame(self.page2)
        self.frame2.setFrameShape(QFrame.Box)
        self.frame2.setFrameShadow(QFrame.Raised)
        self.frame2.setLineWidth(1)
        self.mesh_create = QPushButton(self.frame2)
        self.mesh_create.setCheckable(True)
        self.mesh_create.setObjectName("mesh_create")
        self.mesh_create.setText('Create')
        self.mesh_create.setFont(QtGui.QFont('Microsoft YaHe', 11))
        self.mesh_delete = QPushButton(self.frame2)
        self.mesh_delete.setCheckable(True)
        self.mesh_delete.setObjectName("node_create")
        self.mesh_delete.setText('Delete')
        self.mesh_delete.setFont(QtGui.QFont('Microsoft YaHe', 11))
        self.VLayout2 = QVBoxLayout(self.frame2)
        self.VLayout2.addWidget(self.mesh_create)
        self.VLayout2.addWidget(self.mesh_delete)
        self.VLayout2.setContentsMargins(15, 0, 50, 205)
        self.HLayout2.addWidget(self.frame2)


    def closeEvent(self, event):
        self.dialogSignal.emit('1')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Win_mesh_edit()
    window.show()
    sys.exit(app.exec_())
