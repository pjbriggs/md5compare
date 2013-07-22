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
import sys
import version
version = version.__version__

# Scripts (platform-specific)
scripts = ['compare.py','go_compare.py']
if sys.platform[:3] == 'win':
    # Windows-specific extras
    # Borrowed from
    # https://bitbucket.org/fenics-project/ffc/src/5d7e04c5470b4a2da37ff33b3c43c38cd2ee1d62/setup.py?at=master
    # As the Windows command prompt can't execute Python scripts without a
    # .py extension, create batch files that run the scripts
    batch_files = []
    for script in scripts:
        batch_file = os.path.splitext(script)[0] + ".bat"
        f = open(batch_file, "w")
        f.write('python "%%~dp0\%s" %%*\n' % os.path.split(script)[1])
        f.close()
        batch_files.append(batch_file)
    scripts.extend(batch_files)
    # Also add the Windows postinstall.py script so we can do
    # python setup.py bdist_wininst --install-script postinstall.py
    # to make a Windows installer
    scripts.append("postinstall.py")

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
    scripts = scripts,
    )
