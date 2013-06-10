#!/bin/env python
#
# UI for the compare program
#
import sys
import os
import logging
import time
import webbrowser
import compare
from PyQt4 import QtCore
from PyQt4 import QtGui

class Window(QtGui.QWidget):
    def __init__(self,parent=None):
        # Initialise base class
        QtGui.QWidget.__init__(self,parent)
        # Build the user interface
        self.selectFrom = DirSelectionLine(tooltip="Select the source ('from') directory")
        self.selectTo = DirSelectionLine(tooltip="Select the target ('to') directory to compare")
        self.selectOutput = FileSelectionLine(tooltip="Specify a file to write the final report to")
        # Connect signals to slots for the selection widgets
        self.connect(self.selectFrom,QtCore.SIGNAL("updated_selection(QString)"),
                     self.resetUi)
        self.connect(self.selectTo,QtCore.SIGNAL("updated_selection(QString)"),
                     self.resetUi)
        self.connect(self.selectOutput,QtCore.SIGNAL("updated_selection(QString)"),
                     self.resetUi)
        # Put selection lines into a form layout
        self.selectForm = QtGui.QFormLayout()
        self.selectForm.addRow("From",self.selectFrom)
        self.selectForm.addRow("To",self.selectTo)
        self.selectForm.addRow("Output",self.selectOutput)
        # Progress and status bars
        self.progressBar = QtGui.QProgressBar(self)
        self.statusBar = QtGui.QLabel()
        self.statusMessage = ''
        # Timing comparison operation
        self.timer = QtCore.QTimer()
        self.connect(self.timer,QtCore.SIGNAL("timeout()"),self.updateStatus)
        self.startTime = None
        # Buttons
        self.startButton = QtGui.QPushButton(self.tr("&Start"))
        self.stopButton = QtGui.QPushButton(self.tr("Sto&p"))
        self.quitButton = QtGui.QPushButton(self.tr("&Quit"))
        # Put buttons into a box
        buttons = QtGui.QHBoxLayout()
        buttons.addWidget(self.startButton)
        buttons.addWidget(self.stopButton)
        buttons.addWidget(self.quitButton)
        buttons.addStretch(1)
        # Connect signals to slots for the buttons
        self.startButton.clicked.connect(self.startComparison)
        self.stopButton.clicked.connect(self.stopComparison)
        self.quitButton.clicked.connect(QtCore.QCoreApplication.instance().quit)
        # Build the layout
        layout = QtGui.QVBoxLayout()
        layout.addLayout(self.selectForm)
        layout.addWidget(self.progressBar)
        layout.addWidget(self.statusBar)
        layout.addLayout(buttons)
        layout.addStretch(1)
        self.setLayout(layout)
        self.setWindowTitle(self.tr("Go Compare: Md5 sum checker"))
        self.setMinimumWidth(600)
        # Ensure buttons are in the correct initial state
        self.updateUi()
        # Create worker thread
        self.thread = Worker()
        self.thread.finished.connect(self.finishComparison)
        self.connect(self.thread,QtCore.SIGNAL("update_progress(float)"),self.updateProgress)
        self.connect(self.thread,QtCore.SIGNAL("update_status(QString)"),self.updateStatus)

    def resetUi(self):
        # Define the resetUi slot
        # Clear the status and progress bars
        self.updateStatus("")
        self.updateProgress(0)
        # Validate file/directory selections
        self.validateInputs()

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
        self.updateUi()
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

    def updateProgress(self,value):
        # Update the progress bar
        self.progressBar.setValue(value)

    def validateInputs(self,text=None):
        # Define validateInputs slot
        # Check that inputs are valid and update the UI accordingly
        if os.path.isdir(self.selectFrom.selected) and \
                os.path.isdir(self.selectTo.selected) and \
                self.selectOutput.selected:
            self.startButton.setEnabled(True)
        else:
            self.startButton.setEnabled(False)

    def updateStatus(self,msg=None):
        # Update the status label
        # Process incoming status
        if msg is not None:
            self.statusMessage = str(msg)
        if self.statusMessage.startswith("Examining"):
            if not self.timer.isActive():
                # Start timer
                self.startTime = time.time()
                self.timer.start(1000)
        else:
            if self.timer.isActive():
                # Stop the timer
                self.timer.stop()
        # Construct the message to display
        status_msg = self.statusMessage
        if self.timer.isActive():
            # Prepend elapsed time
            status_msg = "[Elapsed %s] %s" % (self.getElapsedTime(),status_msg)
        self.statusBar.setText(status_msg)

    def getElapsedTime(self):
        # Return the elapsed time since the comparison started
        elapsed_time = time.time()-self.startTime
        ret = []
        days = int(elapsed_time/24.0/60.0/60.0)
        if days > 0:
            ret.append("%d days" % days)
        hours = int(elapsed_time/60.0/60.0) - days*24
        if hours > 0:
            ret.append("%d hrs" % hours)
        minutes = int(elapsed_time/60.0) - (hours+days*24)*60
        if minutes > 0:
            ret.append("%d mins" % minutes)
        if days == 0 and hours == 0:
            seconds = elapsed_time - (minutes+(hours+days*24)*60)*60
            ret.append("%ds" % seconds)
        return ' '.join(ret)

    def updateUi(self):
        # Define the updateUi slot
        # This re-enables the start button etc
        self.startButton.setEnabled(False)
        self.stopButton.setEnabled(False)
        self.selectFrom.setEnabled(True)
        self.selectTo.setEnabled(True)
        self.selectOutput.setEnabled(True)
        # Check if the inputs are still valid
        self.validateInputs()

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
    def __init__(self,name=None,tooltip=None):
        super(SelectionLine,self).__init__()
        # Widgets
        self.selectedLine = QtGui.QLineEdit()
        if tooltip is not None:
            self.selectedLine.setToolTip(tooltip)
        # Container for line contents
        hbox = QtGui.QHBoxLayout()
        # Line contents
        if name is not None:
            # Optional label
            label = QtGui.QLabel("%s" % name)
            label.setFixedWidth(40)
        # Selection dialog
        self.showDialogButton = QtGui.QPushButton("Select",self)
        self.showDialogButton.setToolTip("Select file/directory to use")
        self.showDialogButton.clicked.connect(self.showDialog)
        # Put them together
        if name is not None:
            hbox.addWidget(label)
        hbox.addWidget(self.selectedLine)
        hbox.addWidget(self.showDialogButton)
        self.setLayout(hbox)
        # Connect the 
        self.selectedLine.textChanged.connect(self.updated)

    @property
    def selected(self):
        return str(self.selectedLine.text())

    def _set_selected(self,value):
        self.selectedLine.setText(str(value))
        # Send signal indicating selection was updated
        ##self.emit(QtCore.SIGNAL("updated_selection(QString)"),
        ##          QtCore.QString(self.selected))

    def updated(self,text):
        self.emit(QtCore.SIGNAL("updated_selection(QString)"),text)

    def setEnabled(self,enabled):
        self.selectedLine.setEnabled(enabled)
        self.showDialogButton.setEnabled(enabled)

    def showDialog(self):
        raise NotImplemented("Subclass must implement showDialog")

class FileSelectionLine(SelectionLine):
    def __init__(self,name=None,tooltip=None):
        super(FileSelectionLine,self).__init__(name,tooltip)

    def showDialog(self):
        dialog = QtGui.QFileDialog()
        dialog.setFileMode(QtGui.QFileDialog.AnyFile);
        new_selection = str(dialog.getSaveFileName(self,'Open file',))
        if new_selection:
            self._set_selected(os.path.abspath(new_selection))

class DirSelectionLine(SelectionLine):
    def __init__(self,name=None,tooltip=None):
        super(DirSelectionLine,self).__init__(name,tooltip)

    def showDialog(self):
        new_selection = QtGui.QFileDialog.getExistingDirectory(self,'Select directory',)
        if new_selection:
            self._set_selected(new_selection)

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
