import sys

from PyQt5 import QtGui
from PyQt5.QtCore import QCoreApplication, QMetaObject
from PyQt5.QtWidgets import QWidget, QFrame, QVBoxLayout, QApplication, QTextBrowser


class Win_aboutus(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('About-ImgMesh')
        self.setWindowIcon(QtGui.QIcon(":/icon/set.png"))
        self.setFixedSize(350, 120)

        self.verticalLayout = QVBoxLayout(self, spacing=0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)

        self.frame = QFrame(self)
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.frame.setObjectName("frame")
        self.verticalLayout_2 = QVBoxLayout(self.frame)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.textEdit = QTextBrowser(self.frame)
        self.verticalLayout_2.addWidget(self.textEdit)
        self.verticalLayout.addWidget(self.frame)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)

        self.retranslateUi()
        QMetaObject.connectSlotsByName(self)

    def retranslateUi(self):
        _translate = QCoreApplication.translate
        self.textEdit.setHtml(_translate("Form",
                                         "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
                                         "<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
                                         "p, li { white-space: pre-wrap; }\n"
                                         "</style></head><body style=\" font-family:\'Times New Roman\'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
                                         "<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:11pt; font-weight:600;\">    </span></p>\n"
                                         "<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:11pt; font-weight:600;\">  ImgMesh Version 1.0</span></p>\n"
                                         "<p align=\"justify\" style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p>\n"
                                         "<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:11pt;\">    Author      : Xuanxin Tian</span></p>\n"
                                         "<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:11pt;\">    Contact us: 3120205858@bit.edu.cn</span></p></body></html>"))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    MainWindow = Win_aboutus()
    MainWindow.show()
    sys.exit(app.exec_())
