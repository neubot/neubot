# neubot/rootdir.py

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

''' This module tells you where the web pages are '''

import os.path

# $ROOTDIR/neubot/rootdir.py -> $ROOTDIR
ROOTDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#
# When there is a library.zip web pages are in the same directory,
# and this happens with py2exe.  Otherwise, web pages are in the dir
# that also contains Neubot sources.
#
#
if ROOTDIR.endswith('library.zip') and os.path.isfile(ROOTDIR):
    ROOTDIR = os.path.dirname(ROOTDIR)
    WWW = os.sep.join([ROOTDIR, 'www'])
else:
    WWW = os.sep.join([ROOTDIR, 'neubot/www'])

if __name__ == "__main__":
    print(WWW)
