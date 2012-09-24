#!/usr/bin/env python

#
# Copyright (c) 2011 Simone Basso <bassosimone@gmail.com>,
#  NEXA Center for Internet & Society at Politecnico di Torino
#
# This file is part of Neubot <http://www.neubot.org/>.
#
# Neubot is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Neubot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Neubot.  If not, see <http://www.gnu.org/licenses/>.
#

'''
 Standard setup.py script with py2exe hooks, in order
 to generate an installer for Windows.
'''

import hashlib
import subprocess
import distutils.core
import os.path
import shutil
import sys
import tarfile
import glob

try:
    import py2exe
except ImportError:
    sys.exit('Please install py2exe.')

# To toplevel dir ($TOP/Win32/setup.py -> $TOP)
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Copied from scripts/cksum.py
def cksum_path(path, aarg):
    ''' Computes cksum of a given path '''
    cksum = hashlib.new(aarg)
    filep = open(path, 'rb')
    cksum.update(filep.read())
    return '%s  %s\n' % (cksum.hexdigest(), path)

CONSOLE = [{
    "icon_resources": [(0, "neubot/www/favicon.ico")],
    "script": "Win32/neubot",
}]

PACKAGES = [
    "neubot",
]

#
# Packages are directories below neubot/ but be
# careful because at least neubot/www is not a
# package and contains data.  So make sure that
# there is '__init__.py' before adding a dir.
#
for ENTRY in glob.glob("neubot/*"):
    if os.path.isdir(ENTRY):
        __init = os.sep.join([ENTRY, "__init__.py"])
        if os.path.isfile(__init):
            PACKAGES.append(ENTRY)

PACKAGE_DATA = []

#
# Fill PACKAGE_DATA with file names (not globs) and
# make sure we remove the leading 'neubot/' or we are
# not going to install any package data.
#
def fill_package_data(entry):
    ''' Fill PACKAGE_DATA list with file names '''
    if os.path.isdir(entry):
        for string in glob.glob(os.sep.join([entry, "*"])):
            fill_package_data(string)
    else:
        PACKAGE_DATA.append(entry.replace("neubot/", ""))

fill_package_data("neubot/www")

SCRIPTS = [
    "Win32/neubot",
    "Win32/neubotw",
]

WINDOWS = [{
    "icon_resources": [(0, "neubot/www/favicon.ico")],
    "script": "Win32/neubotw",
}]

RUN_PY2EXE = False
if os.name == "nt" and len(sys.argv) == 1 and py2exe:
    sys.argv.append("py2exe")
    RUN_PY2EXE = True

distutils.core.setup(name="neubot",
                     description="the network neutrality bot",
                     license="GPLv3",
                     packages=PACKAGES,
                     package_data={"neubot": PACKAGE_DATA},
                     version="0.4.15",
                     author="Simone Basso",
                     author_email="bassosimone@gmail.com",
                     windows=WINDOWS,
                     console=CONSOLE,
                     url="http://www.neubot.org/",
                     scripts=SCRIPTS,
                    )

if RUN_PY2EXE:
    IGNORER = shutil.ignore_patterns('.DS_Store')
    shutil.copytree("neubot/www", "dist/www", ignore=IGNORER)
    shutil.copy('Win32/openssl.exe', 'dist/')
    shutil.copy('pubkey.pem', 'dist/')

    if "PROGRAMFILES" in os.environ:
        MAKENSIS = os.environ["PROGRAMFILES"] + "\\NSIS\\makensis.exe"
        if os.path.exists(MAKENSIS):

            #
            # Use standard input because NSIS has the bad habit
            # of performing a chdir(2) in the directory where its
            # script is located.
            #
            FILEP = open('Win32/neubot.nsi')
            subprocess.call([MAKENSIS, '/DUNINST' , '-'], stdin=FILEP)
            FILEP.close()

            subprocess.call(['uninstaller-generator.exe'])

            FILEP = open('Win32/neubot.nsi')
            subprocess.call([MAKENSIS, '-'], stdin=FILEP)
            FILEP.close()

    # Create tarball for auto-update
    shutil.copytree('dist', '0.004015999')
    TARBALL = tarfile.open('0.004015999.tar.gz', 'w:gz')
    TARBALL.add('0.004015999')
    TARBALL.close()

    # Create SHA256 sum
    CKSUM = cksum_path('0.004015999.tar.gz', 'sha256')
    CKSUMFILE = open('0.004015999.tar.gz.sha256', 'wb')
    CKSUMFILE.write(CKSUM)
    CKSUMFILE.close()

    #
    # Move results into wdist and wdist/win32.  We keep in
    # wdist/win32 stuff that must be deployed on the website
    # and in wdist alone all the rest.
    #
    os.mkdir('wdist')
    os.mkdir('wdist/win32')
    shutil.move('uninstaller-generator.exe', 'wdist')
    shutil.move('neubot-0.4.15-setup.exe', 'wdist')
    shutil.move('0.004015999', 'wdist')
    shutil.move('0.004015999.tar.gz', 'wdist/win32')
    shutil.move('0.004015999.tar.gz.sha256', 'wdist/win32')
