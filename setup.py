# setup.py

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

#
# This is a standard setup.py script with py2exe hooks in order
# to generate an installer for Windows.  Please note that the code
# in this file, for now, is effective on Windows only, and that
# some more work is required in order to use this file for Linux
# and other Unixes.  However, the goal is to use this file and
# to reduce the amount of code in Makefile.
#

import subprocess
import distutils.core
import os.path
import shutil
import sys
import glob

try:
    import py2exe
except ImportError:
    py2exe = None

CONSOLE = [{
    "icon_resources": [(0, "icons/neubot.ico")],
    "script": "bin/neubot",
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
for entry in glob.glob("neubot/*"):
    if os.path.isdir(entry):
        __init = os.sep.join([entry, "__init__.py"])
        if os.path.isfile(__init):
            PACKAGES.append(entry)

PACKAGE_DATA = []

#
# Fill PACKAGE_DATA with file names (not globs) and
# make sure we remove the leading 'neubot/' or we are
# not going to install any package data.
#
def fill_package_data(entry):
    if os.path.isdir(entry):
        for s in glob.glob(os.sep.join([entry, "*"])):
            fill_package_data(s)
    else:
        PACKAGE_DATA.append(entry.replace("neubot/", ""))

fill_package_data("neubot/www")

SCRIPTS = [
    "bin/start-neubot-daemon",
    "bin/nagios-plugin-neubot",
    "bin/neubot",
    "bin/neubotw",
]

WINDOWS = [{
    "icon_resources": [(0, "icons/neubot.ico")],
    "script": "bin/neubotw",
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
                     version="0.4.2",
                     author="Simone Basso",
                     author_email="bassosimone@gmail.com",
                     windows=WINDOWS,
                     console=CONSOLE,
                     url="http://www.neubot.org/",
                     scripts=SCRIPTS,
                    )

if RUN_PY2EXE:
    shutil.copytree("neubot/www", "dist/www")
    if "PROGRAMFILES" in os.environ:
        MAKENSIS = os.environ["PROGRAMFILES"] + "\\NSIS\\makensis.exe"
        if os.path.exists(MAKENSIS):
            subprocess.call([MAKENSIS, "neubot.nsi"])
