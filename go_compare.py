#!/bin/env python
#
#     go_compare.py: PyQt GUI for the compare utility
#     Copyright (C) University of Manchester 2013 Peter Briggs
#
########################################################################
#
# go_compare.py
#
#########################################################################

"""go_compare

A PyQT GUI for the compare utility.

"""

#######################################################################
# Module metadata
#######################################################################

import version
__version__ = version.__version__

#######################################################################
# Import modules that this module depends on
#######################################################################

import sys
import os
import logging
import time
import webbrowser
import compare
from PyQt4 import QtCore
from PyQt4 import QtGui

#######################################################################
# Classes
#######################################################################

class Window(QtGui.QWidget):
    """Class defining the main window for the compare GUI

    """
    def __init__(self,parent=None):
        """Create a new Window instance

        """
        # Initialise base class
        QtGui.QWidget.__init__(self,parent)
        # Build the user interface
        self.selectFrom = DirSelectionLine(tooltip="Select the source ('from') directory")
        self.selectTo = DirSelectionLine(tooltip="Select the target ('to') directory to compare")
        self.selectOutput = FileSelectionLine(tooltip="Specify a file to write the final report to")
        # Connect signals to slots for the selection widgets
        self.selectFrom.selectionChanged.connect(self.resetUi)
        self.selectTo.selectionChanged.connect(self.resetUi)
        self.selectOutput.selectionChanged.connect(self.resetUi)
        # Put selection lines into a form layout
        self.selectForm = QtGui.QFormLayout()
        self.selectForm.addRow("From",self.selectFrom)
        self.selectForm.addRow("To",self.selectTo)
        self.selectForm.addRow("Output",self.selectOutput)
        # Checkbutton for ordering in "natural sort order"
        self.useNaturalSort = QtGui.QCheckBox("Use Windows Explorer natural sort order",self)
        self.useNaturalSort.setToolTip("Sorts files with numerical indices into "
                                       "human-readable order")
        # Progress and status bars
        self.progressBar = QtGui.QProgressBar(self)
        self.statusBar = QtGui.QLabel()
        self.statusMessage = ''
        # Timing comparison operation
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.updateStatus)
        self.startTime = None
        # Buttons
        self.startButton = QtGui.QPushButton(self.tr("&Start"))
        self.stopButton = QtGui.QPushButton(self.tr("Sto&p"))
        self.quitButton = QtGui.QPushButton(self.tr("&Quit"))
        self.aboutButton = QtGui.QPushButton(self.tr("&About"))
        # Put buttons into a box
        buttons = QtGui.QHBoxLayout()
        buttons.addWidget(self.startButton)
        buttons.addWidget(self.stopButton)
        buttons.addWidget(self.aboutButton)
        buttons.addWidget(self.quitButton)
        buttons.addStretch(1)
        # Connect signals to slots for the buttons
        self.startButton.clicked.connect(self.startComparison)
        self.stopButton.clicked.connect(self.stopComparison)
        self.quitButton.clicked.connect(QtCore.QCoreApplication.instance().quit)
        self.aboutButton.clicked.connect(self.about)
        # Build the layout
        layout = QtGui.QVBoxLayout()
        layout.addLayout(self.selectForm)
        layout.addWidget(self.useNaturalSort)
        layout.addWidget(self.progressBar)
        layout.addWidget(self.statusBar)
        layout.addLayout(buttons)
        layout.addStretch(1)
        self.setLayout(layout)
        self.setWindowTitle(self.tr("Go Compare v%s: Md5 sum checker" % __version__))
        self.setMinimumWidth(600)
        # Ensure buttons are in the correct initial state
        self.updateUi()
        # Create worker thread
        self.thread = CompareWorker()
        self.thread.finished.connect(self.finishComparison)
        self.thread.progress_update.connect(self.updateProgress)
        self.thread.status_update.connect(self.updateStatus)

    @QtCore.pyqtSlot()
    def resetUi(self):
        """Reset the state of the status and progress bars

        """
        # Define the resetUi slot
        # Clear the status and progress bars
        self.updateStatus("")
        self.updateProgress(0)
        # Validate file/directory selections
        self.validateInputs()

    @QtCore.pyqtSlot()
    def startComparison(self):
        """Start running the directory comparison

        """
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
        # Set the sort key function
        if self.useNaturalSort.isChecked():
            sort_key = compare.SortKeys.natural
        else:
            sort_key = compare.SortKeys.default
        # Do the comparison
        self.thread.compare(from_dir,to_dir,output,sort_key=sort_key)

    @QtCore.pyqtSlot()
    def stopComparison(self):
        """Stop a running comparison process

        """
        # Define stopComparison slot
        # This stops a running comparison
        if self.thread.isRunning():
            logging.debug("Terminating running application")
            self.thread.terminate() # Not supposed to do this
        # Update status
        self.updateStatus("Comparison stopped")
        self.updateUi()

    @QtCore.pyqtSlot()
    def finishComparison(self):
        """Handle the result of a completed comparison

        """
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

    @QtCore.pyqtSlot()
    def about(self):
        """Present an 'about' window

        """
        QtGui.QMessageBox.information(self,
                                      self.tr("About GoCompare"),
                                      self.tr("GoCompare: Version %s\nCopyright (C) University of Manchester 2013 Peter Briggs" % __version__))

    @QtCore.pyqtSlot(float)
    def updateProgress(self,value):
        """Update the progress bar

        Arguments:
          value: new value to set the progress bar to

        """
        self.progressBar.setValue(value)

    @QtCore.pyqtSlot()
    @QtCore.pyqtSlot(QtCore.QString)
    def updateStatus(self,msg=None):
        """Update the status bar

        Arguments:
          msg: if supplied, is the progress message received from
            a running comparison.

        """
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

    def validateInputs(self,text=None):
        # Check that inputs are valid and update the UI accordingly
        if os.path.isdir(self.selectFrom.selected) and \
                os.path.isdir(self.selectTo.selected) and \
                self.selectOutput.selected:
            self.startButton.setEnabled(True)
        else:
            self.startButton.setEnabled(False)

    def getElapsedTime(self):
        """Return the elapsed time since the comparison started

        Returns the elapsed time as a string, giving the time as 
        days, hours, minutes and seconds as appropriate.

        """
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
        """Update the state of the UI when a comparison isn't running

        """
        # Reset button states to default
        self.startButton.setEnabled(False)
        self.stopButton.setEnabled(False)
        self.selectFrom.setEnabled(True)
        self.selectTo.setEnabled(True)
        self.selectOutput.setEnabled(True)
        self.selectFrom.setFocus()
        # Check if the inputs are still valid
        self.validateInputs()

class CompareWorker(QtCore.QThread):
    """Class wrapping Compare object in a Qt thread

    Enables a comparison to be run as a separate thread from
    the GUI, so that the interface isn't blocked.

    Usage is:
    >>> # Create new thread instance
    >>> thread = CompareWorker()
    >>> # Do the comparison
    >>> thread.compare('dir1','dir2','report.txt')

    This class defines the following custom signals:

    status_update(QString): emitted when the status of the
      comparison is updated; the status message is sent as
      a QString object.
    progress_update(float): emitted when the percentage
      progress of the comparison is updated; the percentage
      progress is sent as a float between 0 and 100.0.

    """

    # Define custom signals
    status_update = QtCore.pyqtSignal('QString')
    progress_update = QtCore.pyqtSignal('float')

    def __init__(self,parent=None):
        """Create new CompareWorker instance
        """
        QtCore.QThread.__init__(self,parent)
        self.exiting = False

    def __del__(self):
        self.exiting = True
        self.wait()

    def compare(self,from_dir,to_dir,output,sort_key=None):
        """Run a comparison of two directories

        Arguments:
          from_dir: 'source' directory
          to_dir:   'target' directory being compared to the source
          output:   name of a file to write the comparison report to
          sort_key: optional, function to use for sorting
        """
        self.from_dir = from_dir
        self.to_dir = to_dir
        self.output = output
        self.sort_key = sort_key
        self.start()

    def progress_handler(self,msg):
        """Callback function invoked by the running comparison

        This is passed to the 'Compare' object that runs the comparison
        as a callback that is invoked when progress updates are issued.
        The progress messages are processed and emitted as a Qt signal
        in the main application.

        Arguments:
          msg: message text with progress update from the running
            Compare object

        """
        # Called each time the compare function sends an update
        if msg.startswith("Examining"):
            n = float(msg.split()[1].split('/')[0])
            m = float(msg.split()[1].split('/')[1])
            # Signal that progress has changed
            self.progress_update.emit(float(n/m*100.0))
        # Signal latest status message
        self.status_update.emit(QtCore.QString(msg))

    def run(self):
        """Implement the 'run' method of the base class

        Note: This is never called directly. It is called by Qt once the
        thread environment has been set up.

        """
        compare.Compare(self.from_dir,self.to_dir,
                        report_progress=True,
                        report_every=1,
                        progress_callback=self.progress_handler,
                        sort_key=self.sort_key).report(self.output)
        # Finished, signal that we've reach 100% complete
        self.progress_update.emit(float(100))

class SelectionLine(QtGui.QWidget):
    """Base class for creating file/directory selection widgets

    Creates a composite widget consisting of a line displaying the
    currently selected file or directory, plus a button to invoke
    a selection dialog.

    The SelectionLine class should not be instantiated directly,
    instead it should be subclassed, with the subclass implementing
    the showDialog method to bring up an appropriate selection
    dialog.

    This class defines the following custom signals:

    selectionChanged(Qstring): emitted when the text in the selection
      line changes, either from the selection dialog or from manual
      editing.

    """

    # Define custom signals
    selectionChanged = QtCore.pyqtSignal('QString')

    def __init__(self,name=None,tooltip=None):
        """Create a SelectionLine instance

        """
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
        # Make change to text trigger the selectionChanged signal
        self.selectedLine.textChanged.connect(self.selectionChanged.emit)

    @property
    def selected(self):
        """Return the current selection

        """
        return str(self.selectedLine.text())

    def _set_selected(self,value):
        """Set the selected file or directory

        """
        self.selectedLine.setText(str(value))

    def setEnabled(self,enabled):
        """Enable/disable widget

        If 'enabled' is True then the selection line is editable
        and the file selection button is clickable; if it is True
        then both the widgets are put into a disabled state.

        """
        self.selectedLine.setEnabled(enabled)
        self.showDialogButton.setEnabled(enabled)

    def setFocus(self):
        """Give the widget focus

        Sets focus on the SelectionLine widget (specifically the
        showDialog button).

        """
        self.showDialogButton.setFocus()

    def showDialog(self):
        """Bring up appropriate dialog and process the result

        Placeholder method that should be implemented by the subclass.

        """
        raise NotImplemented("Subclass must implement showDialog")

class FileSelectionLine(SelectionLine):
    """Composite widget for selecting a file

    Subclass implementing a SelectionLine.

    """
    def __init__(self,name=None,tooltip=None):
        """Create a new FileSelectionLine instance

        """
        super(FileSelectionLine,self).__init__(name,tooltip)

    def showDialog(self):
        """Bring up file selection dialog

        """
        dialog = QtGui.QFileDialog()
        dialog.setFileMode(QtGui.QFileDialog.AnyFile);
        new_selection = str(dialog.getSaveFileName(self,'Open file',))
        if new_selection:
            self._set_selected(os.path.abspath(new_selection))

class DirSelectionLine(SelectionLine):
    """Composite widget for selecting a file

    Subclass implementing a SelectionLine.

    """
    def __init__(self,name=None,tooltip=None):
        """Create a new FileSelectionLine instance

        """
        super(DirSelectionLine,self).__init__(name,tooltip)

    def showDialog(self):
        """Bring up file selection dialog

        """
        new_selection = QtGui.QFileDialog.getExistingDirectory(self,'Select directory',)
        if new_selection:
            self._set_selected(new_selection)

#######################################################################
# Functions
#######################################################################

# None defined

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
