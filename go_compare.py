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
        # Build the user interface
        self.selectFrom = DirSelectionLine("From")
        self.selectTo = DirSelectionLine("To")
        self.progressBar = QtGui.QProgressBar(self)
        self.statusBar = QtGui.QLabel()
        self.startButton = QtGui.QPushButton(self.tr("&Start"))
        self.stopButton = QtGui.QPushButton(self.tr("Sto&p"))
        self.quitButton = QtGui.QPushButton(self.tr("&Quit"))
        # Put buttons into a box
        buttons = QtGui.QHBoxLayout()
        buttons.addWidget(self.startButton)
        buttons.addWidget(self.stopButton)
        buttons.addWidget(self.quitButton)
        # Connect signals to slots
        self.startButton.clicked.connect(self.startComparison)
        self.stopButton.clicked.connect(self.stopComparison)
        self.quitButton.clicked.connect(QtCore.QCoreApplication.instance().quit)
        # Build the layout
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.selectFrom)
        layout.addWidget(self.selectTo)
        layout.addWidget(self.progressBar)
        layout.addWidget(self.statusBar)
        layout.addLayout(buttons)
        self.setLayout(layout)
        self.setWindowTitle(self.tr("Go Compare"))
        # Ensure buttons are in the correct initial state
        self.updateUi()
        # Create worker thread
        self.thread = Worker()
        self.thread.finished.connect(self.updateUi)
        self.connect(self.thread,QtCore.SIGNAL("update_progress(float)"),self.updateProgress)
        self.connect(self.thread,QtCore.SIGNAL("update_status(QString)"),self.updateStatus)

    def startComparison(self):
        # Define startComparison slot
        # This disables the start button etc and initiates the comparison
        self.startButton.setEnabled(False)
        self.stopButton.setEnabled(True)
        self.selectFrom.setEnabled(False)
        self.selectTo.setEnabled(False)
        self.progressBar.setValue(0)
        from_dir = self.selectFrom.selected_dir
        to_dir = self.selectTo.selected_dir
        self.thread.compare(from_dir,to_dir)

    def stopComparison(self):
        # Define stopComparison slot
        # This stops a running comparison
        if self.thread.isRunning():
            print "Terminating running application"
            self.thread.terminate() # Not supposed to do this
        self.updateUi()

    def updateProgress(self,value):
        # Update the progress bar
        self.progressBar.setValue(value)

    def updateStatus(self,msg):
        # Update the status label
        self.statusBar.setText(msg)

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

    def update_progress(self,msg):
        # Called each time the compare function sends an update
        if msg.startswith("Done"):
            n = float(msg.split()[1].split('/')[0])
            m = float(msg.split()[1].split('/')[1])
            self.emit(QtCore.SIGNAL("update_progress(float)"),float(n/m*100.0))
        self.emit(QtCore.SIGNAL("update_status(QString)"),QtCore.QString(msg))

    def run(self):
        # Note: This is never called directly. It is called by Qt once the
        # thread environment has been set up.
        compare.Compare(self.from_dir,self.to_dir,
                        report_progress=True,
                        progress_callback=self.update_progress).report()
        # Finished, signal that we've reach 100% complete
        self.emit(QtCore.SIGNAL("update_progress(float)"),float(100))
        self.emit(QtCore.SIGNAL("update_status(QString)"),QtCore.QString("Finished"))

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
