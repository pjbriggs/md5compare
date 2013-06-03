#!/bin/env python
#
# UI for the compare program
#
import sys
import os
import compare
from PyQt4 import QtCore
from PyQt4 import QtGui

class Window(QtGui.QWidget):
    def __init__(self,parent=None):
        # Initialise base class
        QtGui.QWidget.__init__(self,parent)
        # Create worker thread
        self.thread = Worker()
        # Build the user interface
        self.selectFrom = DirSelectionLine("From")
        self.selectTo = DirSelectionLine("To")
        self.startButton = QtGui.QPushButton(self.tr("&Start"))
        self.stopButton = QtGui.QPushButton(self.tr("Sto&p"))
        self.quitButton = QtGui.QPushButton(self.tr("&Quit"))
        # Put buttons into a box
        buttons = QtGui.QHBoxLayout()
        buttons.addWidget(self.startButton)
        buttons.addWidget(self.stopButton)
        buttons.addWidget(self.quitButton)
        # Connect signals to slots
        self.connect(self.startButton,QtCore.SIGNAL("clicked()"),self.startComparison)
        self.connect(self.stopButton,QtCore.SIGNAL("clicked()"),self.stopComparison)
        self.connect(self.quitButton,QtCore.SIGNAL("clicked()"),
                     QtCore.QCoreApplication.instance().quit)
        self.connect(self.thread,QtCore.SIGNAL("finished()"),self.updateUi)
        # Build the layout
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.selectFrom)
        layout.addWidget(self.selectTo)
        layout.addLayout(buttons)
        self.setLayout(layout)
        self.setWindowTitle(self.tr("Go Compare"))
        # Ensure buttons are in the correct initial state
        self.updateUi()

    def startComparison(self):
        # Define startComparison slot
        # This disables the start button etc and initiates the comparison
        self.startButton.setEnabled(False)
        self.stopButton.setEnabled(True)
        self.selectFrom.setEnabled(False)
        self.selectTo.setEnabled(False)
        from_dir = self.selectFrom.selected_dir
        to_dir = self.selectTo.selected_dir
        self.thread.compare(from_dir,to_dir)

    def stopComparison(self):
        # Define stopComparison slot
        # This stops a running comparison
        if self.thread.isRunning():
            self.thread.terminate() # Not supposed to do this
        self.updateUi()

    def updateUi(self):
        # Define the updateUi slot
        # This re-enables the start button etc
        self.startButton.setEnabled(True)
        self.stopButton.setEnabled(False)
        self.selectFrom.setEnabled(True)
        self.selectTo.setEnabled(True)

class Worker(QtCore.QThread):
    def __init__(self,parent=None):
        QtCore.QThread.__init__(self,parent)
        self.exiting = False

    def __del__(self):
        self.exiting = True
        self.wait()

    def compare(self,from_dir,to_dir):
        self.from_dir = from_dir
        self.to_dir = to_dir
        self.start()

    def run(self):
        # Note: This is never called directly. It is called by Qt once the
        # thread environment has been set up.
        compare.Compare(self.from_dir,self.to_dir,
                        report_progress=True).report()

class DirSelectionLine(QtGui.QWidget):
    def __init__(self,name):
        super(DirSelectionLine,self).__init__()
        self.dirn = os.getcwd()
        self.selected_dir_label = QtGui.QLineEdit()
        self.selected_dir_label.setMaxLength(1000)
        # Container for line contents
        hbox = QtGui.QHBoxLayout()
        # Line contents: label
        lbl = QtGui.QLabel("%s:" % name)
        lbl.setFixedWidth(40)
        # Selection dialog
        self.showDialogButton = QtGui.QPushButton("Select",self)
        self.showDialogButton.clicked.connect(self.showDialog)
        # Put them together
        hbox.addWidget(lbl)
        hbox.addWidget(self.selected_dir_label)
        hbox.addWidget(self.showDialogButton)
        self.setLayout(hbox)

    @property
    def selected_dir(self):
        return str(self.selected_dir_label.text())

    def showDialog(self):
        dirn = str(QtGui.QFileDialog.getExistingDirectory(self,'Select directory',))
        self.selected_dir_label.setText(dirn)

    def setEnabled(self,enabled):
        self.selected_dir_label.setEnabled(enabled)
        self.showDialogButton.setEnabled(enabled)

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
