# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'global_s.ui'
#
# Created by: PyQt5 UI code generator 5.15.10
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Global(object):
    def setupUi(self, Global):
        Global.setObjectName("Global")
        Global.resize(482, 342)
        font = QtGui.QFont()
        font.setFamily("黑体")
        Global.setFont(font)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/按钮图标/窗体/res/图标.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Global.setWindowIcon(icon)
        self.verticalLayout = QtWidgets.QVBoxLayout(Global)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(Global)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.gridLayout_2 = QtWidgets.QGridLayout()
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.pushButton = QtWidgets.QPushButton(Global)
        self.pushButton.setObjectName("pushButton")
        self.gridLayout_2.addWidget(self.pushButton, 2, 1, 1, 1)
        self.listView = QtWidgets.QListView(Global)
        self.listView.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.listView.setObjectName("listView")
        self.gridLayout_2.addWidget(self.listView, 1, 0, 1, 5)
        self.pushButton_2 = QtWidgets.QPushButton(Global)
        self.pushButton_2.setObjectName("pushButton_2")
        self.gridLayout_2.addWidget(self.pushButton_2, 2, 3, 1, 1)
        self.pushButton_3 = QtWidgets.QPushButton(Global)
        self.pushButton_3.setObjectName("pushButton_3")
        self.gridLayout_2.addWidget(self.pushButton_3, 2, 2, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout_2)

        self.retranslateUi(Global)
        QtCore.QMetaObject.connectSlotsByName(Global)

    def retranslateUi(self, Global):
        _translate = QtCore.QCoreApplication.translate
        Global.setWindowTitle(_translate("Global", "全局参数"))
        self.label.setText(_translate("Global", "资源文件夹路径："))
        self.pushButton.setText(_translate("Global", "添加文件夹"))
        self.pushButton_2.setText(_translate("Global", "删除"))
        self.pushButton_3.setText(_translate("Global", "打开路径"))
import images_rc
