if __name__ == '__main__':
    import sys

    from PyQt5.QtWidgets import QApplication
    from ImgMesh import Win_Main

    app = QApplication(sys.argv)
    MainWindow = Win_Main()
    sys.exit(app.exec_())


