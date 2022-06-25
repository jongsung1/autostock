from kiwoom.kiwoom import *
from PyQt5.QtWidgets import *
import sys

class Ui_class():
    def __init__(self):
        print("UI class")

        self.app = QApplication(sys.argv)

        self.kiwoom = Kiwoom()

        ### 실행 후 종료 안되도록
        self.app.exec_()