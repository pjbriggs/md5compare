"""
postinstallation script when using setup.py to install on
Windows platforms.

Based on https://github.com/nipy/pbrain/blob/master/postinstall.py

"""

import sys, os
import distutils.sysconfig

if sys.platform[:3] != 'win':
    sys.exit()

# Create a desktop shortcut for all users
desktopDir = get_special_folder_path('CSIDL_COMMON_DESKTOPDIRECTORY')

target = os.path.join(distutils.sysconfig.PREFIX,'Scripts','go_compare.bat')
filename = os.path.join(desktopDir, 'go_compare.bat.lnk')

create_shortcut(target, 'Shortcut to go_compare', filename)

print 'Created shortcut from %s to %s' % (filename, target)

