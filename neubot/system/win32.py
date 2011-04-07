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

#
# Code for Win32
#

import os.path
import logging.handlers

class BackgroundLogger(object):

    """Where to log messages when running in background under
       windows -- note we nearly always run in background since
       for windows neubot does not attach to a console."""

    def __init__(self):
        formatter = logging.Formatter("%(message)s")

        # XXX not passing our dllname here
        handler = logging.handlers.NTEventLogHandler("neubot")
        handler.setFormatter(formatter)

        self.logger = logging.Logger("neubot.win32.BackgroundLogger")
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)

    def error(self, message):
        self.logger.error(message)

    def warning(self, message):
        self.logger.warning(message)

    #
    # We don't log at info() and warning() level when
    # running as a windows application under Win32 because
    # that might fill the log and the default policy does
    # not help: it does not rotate logs, but rather it
    # prevents further logging.
    #

    def info(self, message):
        pass

    def debug(self, message):
        pass

def change_dir():
    appdata = os.environ["APPDATA"]
    datadir = os.sep.join([appdata, "neubot"])
    if not os.path.isdir(datadir):
        os.mkdir(datadir, 0755)
    os.chdir(datadir)

def drop_privileges():
    pass

def go_background():
    pass
