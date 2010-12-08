# neubot/unix.py

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
# Code for UNIX
#

import os.path
import sys

# ismacosx()

class _IsMacOSX:

    """
    MacOSX is "posix" and "darwin" but there are significant differences
    from other Unices.  Therefore we need to identify MacOSX to adapt our
    behavior.  For example, MacOSX does not use X11 and therefore we cannot
    check for "DISPLAY" in os.environ to guess whether the graphical user
    interface is available.
    """

    SystemVersion = "/System/Library/CoreServices/SystemVersion.plist"
    ServerVersion = "/System/Library/CoreServices/ServerVersion.plist"

    def __init__(self):
        self.ismacosx = (sys.platform == "darwin" and
         (os.path.exists(self.SystemVersion) or
          os.path.exists(self.ServerVersion)))

    def __call__(self):
        return self.ismacosx

ismacosx = _IsMacOSX()

__all__ = [ "ismacosx" ]

# BackgroundLogger

if os.name == "posix":

    import syslog

    class BackgroundLogger(object):

        """
        We don't use logging.handlers.SysLogHandler because that class
        does not know the name of the UNIX domain socket in use for the
        current operating system.  In many Unices the UNIX domain socket
        name is /dev/log, but this is not true, for example, under the
        Mac.  A better solution seems to use syslog because this is just
        a wrapper to the host syslog library.  And who wrote such lib
        for sure knows the UNIX domain socket location for the current
        operating system.
        """

        def __init__(self):
            syslog.openlog("neubot", syslog.LOG_DAEMON|syslog.LOG_PID)

        def error(self, message):
            syslog.syslog(syslog.LOG_ERR, message)

        def warning(self, message):
            syslog.syslog(syslog.LOG_WARNING, message)

        def info(self, message):
            syslog.syslog(syslog.LOG_INFO, message)

        def debug(self, message):
            syslog.syslog(syslog.LOG_DEBUG, message)

    __all__.append("BackgroundLogger")
