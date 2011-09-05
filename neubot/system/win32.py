# neubot/system/win32.py

#
# Copyright (c) 2010-2011 Simone Basso <bassosimone@gmail.com>,
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

import os.path

def change_dir():
    pass

def _get_profile_dir():
    appdata = os.environ["APPDATA"]
    datadir = os.sep.join([appdata, "neubot"])
    return datadir

def _want_rwx_dir(p, perror=None):
    if not os.path.isdir(p):
        os.mkdir(p, 0755)

def go_background():
    pass

def drop_privileges(perror=None):
    pass

def redirect_to_dev_null():
    pass

def _want_rw_file(path, perror=None):
    # XXX: PyPy doesn't work with this
    open(path, "ab+").close()

def _get_pidfile_dir():
    return None

#
# We tried NT Event Logger but it is not as friendly as
# syslog under Unix.  So we decided to write logs on the
# database only for Windows.
#
def __logger(severity, message):
    pass

def get_background_logger():
    return __logger
