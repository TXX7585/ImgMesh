'''
-*- coding: utf-8 -*-
@Author: Tian
@Email  : 1055067077@qq.com
@Create  : 2023/11/21 14:25
'''
import sys
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget
from PyQt5 import QtWebEngineWidgets


class HelpDoc(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Help")
        self.setFixedSize(1000, 800)
        self.setWindowIcon(QIcon(":/icon/set.png"))
        self.setGeometry(100, 100, 1000, 800)

        layout = QVBoxLayout()
        self.web_view = QtWebEngineWidgets.QWebEngineView(self)

        layout.addWidget(self.web_view)
        self.setLayout(layout)
        self.web_view.load(QUrl.fromLocalFile("/help_doc/manual.html"))

    def handle_anchor_click(self, url):
        self.show_content(url.toString())

    def show_content(self, target):
        self.text_browser.setSource(QUrl(target))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = HelpDoc()
    main_window.show()
    sys.exit(app.exec_())
