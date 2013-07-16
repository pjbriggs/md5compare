"""Description

Setup script to install md5compare: recursive checksum comparison of directory contents

Copyright (C) University of Manchester 2013 Peter Briggs

This code is free software; you can redistribute it and/or modify it
under the terms of the Artistic License 2.0 (see the file LICENSE included
with the distribution).

This will install md5compare and its dependencies and provide the 'compare.py' and
'go_compare.py' commands
"""

from distutils.core import setup
import os
import version
version = version.__version__

setup(
    name = "md5compare",
    version = version,
    description = 'Recursive checksum comparison of directory contents',
    long_description = 'md5compare provides a command-line utility compare.py and a PyQt4 GUI go_compare.py which will perform a recursive comparison of the contents of two directories using MD5 checksums.',
    maintainer = 'Peter Briggs',
    maintainer_email = 'peter.briggs@manchester.ac.uk',
    license = 'Artistic License 2.0',
    url = 'https://github.com/pjbriggs/md5compare',
    py_modules = ['compare','go_compare','version','Md5sum'],
    requires = ['PyQt (>=4.0)',],
    scripts = ['compare.py','go_compare.py'],
    )
