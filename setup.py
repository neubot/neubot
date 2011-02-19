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

try:
   import py2exe
except ImportError:
   py2exe = None

PACKAGES = [
    "neubot/bittorrent",
    "neubot/http",
    "neubot/net",
    "neubot/simplejson",
    "neubot",
]

PACKAGE_DATA = [
    "neubot/www/css",
    "neubot/www/img",
    "neubot/www/js",
    "neubot/www",
]

SCRIPTS = [
    "bin/start-neubot-daemon",
    "bin/neubot",
]

WINDOWS = [{
    "icon_resources": [(0, "icons/neubot.ico")],
    "script": "bin/neubot",
}]

PY2EXE = False
if os.name == "nt" and len(sys.argv) == 1 and py2exe:
    sys.argv.append("py2exe")
    PY2EXE = True

distutils.core.setup(name="neubot",
                     description="the network neutrality bot",
                     license="GPLv3",
                     packages=PACKAGES,
                     package_data={"neubot": PACKAGE_DATA},
                     version="0.3.4",
                     author="Simone Basso",
                     author_email="bassosimone@gmail.com",
                     windows=WINDOWS,
                     url="http://www.neubot.org/",
                     scripts=SCRIPTS,
                    )

if PY2EXE:
    shutil.copytree("neubot/www", "dist/www")
    if "PROGRAMFILES" in os.environ:
        MAKENSIS = os.environ["PROGRAMFILES"] + "\\NSIS\\makensis.exe"
        if os.path.exists(MAKENSIS):
            subprocess.call([MAKENSIS, "neubot.nsi"])
