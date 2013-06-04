#!/bin/env python
#
# UI for the compare program
#
import sys
import os
import logging
import webbrowser
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
        self.selectOutput = FileSelectionLine("Output")
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
        buttons.addStretch(1)
        # Connect signals to slots
        self.startButton.clicked.connect(self.startComparison)
        self.stopButton.clicked.connect(self.stopComparison)
        self.quitButton.clicked.connect(QtCore.QCoreApplication.instance().quit)
        # Build the layout
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.selectFrom)
        layout.addWidget(self.selectTo)
        layout.addWidget(self.selectOutput)
        layout.addWidget(self.progressBar)
        layout.addWidget(self.statusBar)
        layout.addLayout(buttons)
        layout.addStretch(1)
        self.setLayout(layout)
        self.setWindowTitle(self.tr("Go Compare"))
        self.setMinimumWidth(600)
        # Ensure buttons are in the correct initial state
        self.updateUi()
        # Create worker thread
        self.thread = Worker()
        self.thread.finished.connect(self.finishComparison)
        self.connect(self.thread,QtCore.SIGNAL("update_progress(float)"),self.updateProgress)
        self.connect(self.thread,QtCore.SIGNAL("update_status(QString)"),self.updateStatus)

    def startComparison(self):
        # Define startComparison slot
        # This disables the start button etc and initiates the comparison
        self.startButton.setEnabled(False)
        self.stopButton.setEnabled(True)
        self.selectFrom.setEnabled(False)
        self.selectTo.setEnabled(False)
        self.selectOutput.setEnabled(False)
        self.progressBar.setValue(0)
        # Collect the to, from and output selections
        from_dir = self.selectFrom.selected
        to_dir = self.selectTo.selected
        output = self.selectOutput.selected
        if os.path.exists(output):
            # Prompt before overwriting an existing file
            logging.debug("%s already exists" % output)
            ret = QtGui.QMessageBox.warning(self,self.tr("File exists"),
                                            self.tr("File '%s'\nalready exists\nDo you want to overwrite it?" % output),
                                            QtGui.QMessageBox.No | QtGui.QMessageBox.Default,
                                            QtGui.QMessageBox.Yes)
            if ret == QtGui.QMessageBox.No:
                self.updateUi()
                return
            else:
                os.remove(output)
        # Do the comparison
        self.thread.compare(from_dir,to_dir,output)

    def stopComparison(self):
        # Define stopComparison slot
        # This stops a running comparison
        if self.thread.isRunning():
            logging.debug("Terminating running application")
            self.thread.terminate() # Not supposed to do this
        self.updateUi()

    def finishComparison(self):
        # Define finishComparison slot
        # This handles the result of the comparison once it's completed
        # Check that the output file exists
        output = os.path.abspath(self.selectOutput.selected)
        if not os.path.exists(output):
            # No output file
            QtGui.QMessageBox.critical(self,self.tr("Comparison failed"),
                                       self.tr("No output file written for the comparison"))
            self.updateUi()
            return
        # Check the output file for problems
        status = str(self.statusBar.text())
        failed = status.count("failed") > 0
        bad = status.count("bad") > 0
        extra = status.count("extra") > 0
        if failed or bad or extra:
            qbox = QtGui.QMessageBox.critical
        else:
            qbox = QtGui.QMessageBox.information
        ret = qbox(self,self.tr("Comparison completed"),
                   self.tr("Comparison completed:\n\n%s\n\nView the full report?" % status),
                   QtGui.QMessageBox.Yes | QtGui.QMessageBox.Default,
                   QtGui.QMessageBox.No)
        if ret == QtGui.QMessageBox.Yes:
            webbrowser.open("file:%s%s" % (os.sep*2,output))
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
        self.selectOutput.setEnabled(True)

class Worker(QtCore.QThread):
    def __init__(self,parent=None):
        QtCore.QThread.__init__(self,parent)
        self.exiting = False

    def __del__(self):
        self.exiting = True
        self.wait()

    def compare(self,from_dir,to_dir,output):
        self.from_dir = from_dir
        self.to_dir = to_dir
        self.output = output
        self.start()

    def update_progress(self,msg):
        # Called each time the compare function sends an update
        if msg.startswith("Examining"):
            n = float(msg.split()[1].split('/')[0])
            m = float(msg.split()[1].split('/')[1])
            self.emit(QtCore.SIGNAL("update_progress(float)"),float(n/m*100.0))
        self.emit(QtCore.SIGNAL("update_status(QString)"),QtCore.QString(msg))

    def run(self):
        # Note: This is never called directly. It is called by Qt once the
        # thread environment has been set up.
        compare.Compare(self.from_dir,self.to_dir,
                        report_progress=True,
                        report_every=1,
                        progress_callback=self.update_progress).report(self.output)
        # Finished, signal that we've reach 100% complete
        self.emit(QtCore.SIGNAL("update_progress(float)"),float(100))

class SelectionLine(QtGui.QWidget):
    def __init__(self,name):
        super(SelectionLine,self).__init__()
        # Widgets
        self.selectedLine = QtGui.QLineEdit()
        # Container for line contents
        hbox = QtGui.QHBoxLayout()
        # Line contents: label
        label = QtGui.QLabel("%s" % name)
        label.setFixedWidth(40)
        # Selection dialog
        self.showDialogButton = QtGui.QPushButton("Select",self)
        self.showDialogButton.clicked.connect(self.showDialog)
        # Put them together
        hbox.addWidget(label)
        hbox.addWidget(self.selectedLine)
        hbox.addWidget(self.showDialogButton)
        self.setLayout(hbox)

    @property
    def selected(self):
        return str(self.selectedLine.text())

    def _set_selected(self,value):
        self.selectedLine.setText(str(value))

    def setEnabled(self,enabled):
        self.selectedLine.setEnabled(enabled)
        self.showDialogButton.setEnabled(enabled)

    def showDialog(self):
        raise NotImplemented("Subclass must implement showDialog")

class FileSelectionLine(SelectionLine):
    def __init__(self,name):
        super(FileSelectionLine,self).__init__(name)

    def showDialog(self):
        self._set_selected(QtGui.QFileDialog.getOpenFileName(self,'Open file',))

class DirSelectionLine(SelectionLine):
    def __init__(self,name):
        super(DirSelectionLine,self).__init__(name)

    def showDialog(self):
        self._set_selected(QtGui.QFileDialog.getExistingDirectory(self,'Select directory',))

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
