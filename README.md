md5compare
==========

Utilities to recursively compare the contents of two directories, reporting files
that are missing from one or the other and using MD5 sums to check whether common
files are in fact the same.

There are two programs:

 * `compare.py` is a command-line version of the comparison utility
 * `go_compare.py` is a PyQT GUI version

The programs have been developed for Linux and Windows platforms (see "Dependencies"
below).

compare.py
----------

A command-line utility which takes a `FROM` directory and a `TO` directory,
plus (optionally) the name of an output file; it compares the contents of
`FROM` and `TO` and reports the differences (including the presence of any
additional files in `TO` which are not in `FROM`, and vice versa). Files
that are in both `FROM` and `TO` are compared using MD5 sums.

A report will be written to the output file, or to stdout if no file is
specified.

Usage:

    compare.py FROM_DIR TO_DIR [ OUTPUT_FILE ]

Compare contents of a pair of directories using MD5 sums

Options:

    --version           show program's version number and exit
    -h, --help          show this help message and exit
    --progress          report progress
    --use-natural-sort  use 'natural sort order' for ordering files (same as
                        Windows Explorer)


go_compare.py
-------------

A GUI tool built on the `compare` program which allows the user to select
the `FROM` and `TO` directories and the output file using standard, runs the
comparison and then reports the result.

The GUI also reports the progress and elapsed time of a running comparison
(with a big directory it might run for about an hour or more).

Usage:

    python go_compare.py

`go_compare.py` is built on the `PyQt4` libraries so these must be available
on your system.

Dependencies
------------

`compare.py` was developed against Python 2.7; `go_compare.py` additionally
requires PyQt4.

The utilities have been used under Windows XP and Windows 7 using the
following Python and PyQt packages:

 * ActivePython 2.7.2.5: <http://downloads.activestate.com/ActivePython/releases/2.7.2.5/>
 * PyQt 4.10.1: <http://www.riverbankcomputing.co.uk/software/pyqt/download>

Other versions may also work but have not been tried.

Making installers using setup.py
--------------------------------

### Linux RPMs ###

To make a platform-independent RPM installer on Linux do:

    python setup.py bdist_rpm

which will make the RPM in the `dist` subdirectory. It can then be installed
on the system using e.g. `yum install dist/md5compare-0.0.1-1.noarch.rpm`.

### Windows ###

To make a Windows installer do:

    python setup.py bdist_wininst --install-script postinstall.py

(Nb needs to be done on a Windows system).

This will create the installer in the `dist` subdirectory which will install
the md5compare programs into the Python installation and try to create a
desktop shortcut to the graphical interface.

__Nb  the installer should be run as administrator otherwise the shortcut
will not be created.__

The package can be removed at a later date via the `Uninstall programs`
window.


ChangeLog
---------

0.0.4: added options for sorting files into 'natural sort order' (the
       same as used by Windows Explorer).

0.0.3: report MD5 sums for both copies of a file when there is a mismatch

0.0.2: added setup.py for installation on Linux and Windows platforms.

0.0.1: initial version
