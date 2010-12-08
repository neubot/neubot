# neubot/win32.py

#
# Copyright (c) 2010 Simone Basso <bassosimone@gmail.com>,
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

import os

__all__ = []

# BackgroundLogger

if os.name == "nt":

    class BackgroundLogger(object):

        """
        Empty background logger for Windows.  We need to fix this as
        soon as possible and use here some nice class from logging such
        as the rotating logger or, if possible, the native logger for
        Windows.
        """

        def error(self, message):
            pass

        def warning(self, message):
            pass

        def info(self, message):
            pass

        def debug(self, message):
            pass

    __all__.append("BackgroundLogger")
