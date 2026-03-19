import os
import sys

from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt5.QtCore import QUrl


class HelpDialog(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("帮助文档")
        self.setGeometry(100, 100, 1000, 800)
        layout = QVBoxLayout()
        self.web_view = QWebEngineView(self)

        layout.addWidget(self.web_view)
        self.setLayout(layout)
        url = os.getcwd() + os.path.sep + "manual.html"
        self.web_view.load(QUrl.fromLocalFile(url))

    def show_content(self, target):
        self.web_view.load(QUrl.fromLocalFile(target))

if __name__ == "__main__":
    app = QApplication(sys.argv)

    main_window = HelpDialog()
    main_window.show()

    sys.exit(app.exec_())
