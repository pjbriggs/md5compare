md5compare
==========

Utilities to recursively compare the contents of two directories, reporting files
that are missing from one or the other and using MD5 sums to check whether common
files are in fact the same.

There are two programs:

 * `compare.py` is a command-line version of the comparison utility
 * `go_compare.py` is a PyQT GUI version

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

    --version   show program's version number and exit
    -h, --help  show this help message and exit
    --progress  report progress

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



