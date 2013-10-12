# neubot/http/ssi.py

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
 Minimal Server Side Includes (SSI) implementation to help
 the development of the Web User Interface (WUI).
 The code below has been written with an healthy amound
 of prejudice^H^H^H paranoia against Unicode and attempts to
 enforce an ASCII-only policy on all the path names.
'''

# Should be moved to neubot/http_ssi.py

import sys
import os.path
import re

from neubot import utils_path

MAXDEPTH = 8
REGEX = '<!--#include virtual="([A-Za-z0-9./_-]+)"-->'

def ssi_open(rootdir, path, mode):
    ''' Wrapper for open() that makes security checks '''
    path = utils_path.append(rootdir, path, False)
    if not path:
        raise ValueError("ssi: Path name above root directory")
    return open(path, mode)

def ssi_split(rootdir, document, page, count):
    ''' Split the page and perform inclusion '''
    if count > MAXDEPTH:
        raise ValueError("ssi: Too many nested includes")
    include = False
    for chunk in re.split(REGEX, document):
        if include:
            include = False
            filep = ssi_open(rootdir, chunk, "rb")
            ssi_split(rootdir, filep.read(), page, count + 1)
            filep.close()
        else:
            include = True
            page.append(chunk)

def ssi_replace(rootdir, filep):
    ''' Replace with SSI the content of @filep '''
    page = []
    ssi_split(rootdir, filep.read(), page, 0)
    return "".join(page)

if __name__ == "__main__":
    FILEP = open(sys.argv[1], "rb")
    print ssi_replace(os.path.abspath("."), FILEP)
