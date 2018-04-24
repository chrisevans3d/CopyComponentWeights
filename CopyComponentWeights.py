from Qt import QtGui, QtCore, QtWidgets

try:
    import shiboken as shiboken
except:
    import shiboken2 as shiboken

import maya.cmds as cmds
import maya.OpenMayaUI as openMayaUI

def getMayaWindow():
    ptr = openMayaUI.MQtUtil.mainWindow()
    if ptr is not None:
        return shiboken.wrapInstance(long(ptr), QtWidgets.QWidget)


class CopyComponentWeights(QtWidgets.QDialog):
    '''
    Tool to help copy weights between two component selections
    
    import CopyComponentWeights_UI
    CopyComponentWeightsWindow = CopyComponentWeights_UI.show()
    '''

    def __init__(self, parent=getMayaWindow()):
        super(CopyComponentWeights, self).__init__(parent)

        self.from7 = None
        self.to = None
        self.toSkin = None
        self.fromSkin = None

        self.setWindowTitle('CopyComponentWeights')

        # make the main layout
        mainLayout = QtWidgets.QVBoxLayout()

        self.fromBTN = QtWidgets.QPushButton('<<< GET SELECTION')
        self.fromClosestBTN = QtWidgets.QPushButton('<<< GET SELECTION')

        self.fromVertsLBL = QtWidgets.QLabel('FROM COMPONENTS:')
        fromInfoLayout = QtWidgets.QHBoxLayout()
        fromInfoLayout.addWidget(self.fromVertsLBL)
        fromInfoLayout.addWidget(self.fromBTN)

        horizontal_layout_last_buttons = QtWidgets.QHBoxLayout()

        self.toBTN = QtWidgets.QPushButton('<<< GET SELECTION')
        # self.toClosestBTN = QtWidgets.QPushButton('<<< GET CLOSEST VERTS FROM SELECTED MESH')
        self.toVertsLBL = QtWidgets.QLabel('TO COMPONENTS:')
        # self.toSkinLBL = QtWidgets.QLabel('SKIN:')
        toInfoLayout = QtWidgets.QHBoxLayout()
        toInfoLayout.addWidget(self.toVertsLBL)
        # toInfoLayout.addWidget(self.toClosestBTN)
        toInfoLayout.addWidget(self.toBTN)

        # Surface association combobox
        self.surface_association_CMB = QtWidgets.QComboBox()
        self.surface_association_CMB.addItems(['closestPoint', 'rayCast', 'closestComponent', 'uvSpace'])

        a_label1, a_label2, a_label3 = QtWidgets.QLabel('A1:'), QtWidgets.QLabel('A2:'), QtWidgets.QLabel('A3:')
        self.ass1, self.ass2, self.ass3 = QtWidgets.QComboBox(), QtWidgets.QComboBox(), QtWidgets.QComboBox()
        for ass in [self.ass1, self.ass2, self.ass3]:
            ass.addItems(['none', 'closestJoint', 'closestBone', 'oneToOne', 'label', 'name'])

        self.copyBTN = QtWidgets.QPushButton('COPY WEIGHTS')

        mainLayout.addLayout(fromInfoLayout)
        mainLayout.addLayout(toInfoLayout)
        self.setLayout(mainLayout)

        self.selectBTN = QtWidgets.QPushButton('SELECT ONLY')
        self.selectBTN.setMaximumWidth(80)

        # fill final layout
        horizontal_layout_last_buttons.addWidget(self.selectBTN)
        horizontal_layout_last_buttons.addWidget(self.copyBTN)

        # add options
        horizontal_layout_ass = QtWidgets.QHBoxLayout()
        mainLayout.addWidget(self.surface_association_CMB)
        horizontal_layout_ass.addWidget(a_label1)
        horizontal_layout_ass.addWidget(self.ass1)
        horizontal_layout_ass.addWidget(a_label2)
        horizontal_layout_ass.addWidget(self.ass2)
        horizontal_layout_ass.addWidget(a_label3)
        horizontal_layout_ass.addWidget(self.ass3)
        mainLayout.addLayout(horizontal_layout_ass)

        # set defaults
        self.ass1.setCurrentIndex(1)
        self.ass2.setCurrentIndex(3)
        self.ass3.setCurrentIndex(5)

        # connect UI
        self.fromBTN.clicked.connect(self.fillFrom)
        self.toBTN.clicked.connect(self.fillTo)
        self.copyBTN.clicked.connect(self.copyFn)
        self.selectBTN.clicked.connect(self.selectFn)
        # self.toClosestBTN.clicked.connect(self.toClosestFn)

        mainLayout.addLayout(horizontal_layout_last_buttons)

    def findRelatedSkinCluster(self, node):

        skinClusters = cmds.ls(type='skinCluster')

        for cluster in skinClusters:
            geometry = cmds.skinCluster(cluster, q=True, g=True)[0]
            geoTransform = cmds.listRelatives(geometry, parent=True)[0]

            dagPath = cmds.ls(geoTransform, long=True)[0]

            if geoTransform == node:
                return cluster
            elif dagPath == node:
                return cluster

    def fillFrom(self):
        self.from7 = cmds.ls(sl=1, flatten=1)
        mesh = self.from7[0].split('.')[0]
        self.fromVertsLBL.setText('FROM COMPONENTS: ' + mesh + ' (' + str(len(self.from7)) + ')')
        self.fromSkin = self.findRelatedSkinCluster(mesh)

    def fillTo(self):
        self.to = cmds.ls(sl=1, flatten=1)
        mesh = self.to[0].split('.')[0]
        self.toVertsLBL.setText('TO COMPONENTS: ' + mesh + ' (' + str(len(self.to)) + ')')
        self.toSkin = self.findRelatedSkinCluster(mesh)

    def addNeededInfluences(self, fromCluster, toCluster):
        fromInfList = [str(inf) for inf in cmds.skinCluster(fromCluster, inf=1, q=1)]
        toInfList = [str(inf) for inf in cmds.skinCluster(toCluster, inf=1, q=1)]
        for inf in fromInfList:
            if inf not in toInfList:
                cmds.skinCluster(toCluster, e=1, ai=inf, lw=1)
                cmds.setAttr(inf + '.liw', 0)
                print '>>>CopyComponentWeights:', inf, 'added to skinCluster', toCluster

    def copyFn(self):
        if self.from7 and self.to:

            # let's check that all the influences exist on the mesh we're transferring to
            self.addNeededInfluences(self.fromSkin, self.toSkin)

            influence_assoc_tuple = (self.ass1.currentText(), self.ass2.currentText(), self.ass3.currentText())

            cmds.copySkinWeights(self.from7, self.to, ss=self.fromSkin, ds=self.toSkin, noMirror=1,
                                 surfaceAssociation=(surface_association_CMB.currentText()), ia=influence_assoc_tuple)

        else:
            cmds.warning('Must specify two component selections!')

    def selectFn(self):
        cmds.select(cl=1)
        cmds.select(self.from7)
        cmds.select(self.to, add=1)

def showUI():
    global CopyComponentWeightsWindow
    try:
        CopyComponentWeightsWindow.close()
    except:
        pass

    CopyComponentWeightsWindow = CopyComponentWeights()
    CopyComponentWeightsWindow.show()
    return CopyComponentWeightsWindow


if __name__ == '__main__':
    showUI()
