# neubot/log.py
# Copyright (c) 2010 NEXA Center for Internet & Society

# This file is part of Neubot.
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
# Wrapper for logger
#

import collections
import logging.handlers
import time
import traceback

from neubot.compat import deque_append
from os import isatty
from sys import stderr

#
# Make sure we are running MacOS X and not a custom copy
# of OpenDarwin.   XXX Probably this check should be refined
# a bit (i.e., we might want to read the property file to
# be really sure).
# MacOS X is "posix" and "darwin" but is a bit different
# from classical Unices, therefore we need to identify it
# in order to adapt our behavior.
# This code must be here because this is the root module,
# i.e. all other modules import this one.
# 

from sys import platform
from os import path

class IsMacOSX:
    def __init__(self):
        self.ismacosx = (platform == "darwin" and (
          path.exists("/System/Library/CoreServices/SystemVersion.plist")
           or path.exists("/System/Library/CoreServices/ServerVersion.plist")))

    def __call__(self):
        return self.ismacosx

ismacosx = IsMacOSX()

#
# SysLogHandler uses UDP by default.  Or you can configure it to
# use a given UNIX domain socket.  The problem is that the socket
# is /dev/log for most Unices, but not for MacOS X.
#
# Then, if we use SysLogHandler we have to know the path where
# the UNIX domain socket is.  A more portable solution is to use
# syslog wrapper.  Indeed, who wrote syslog for the current system
# of course knows the mechanism employed (i.e., UDP or UNIX domain
# socket), paths, and stuff.
#
# In the long term we want to use syslog wrapper for all Unices,
# but, for now, let's apply the new behavior to MacOS X only.
#

if ismacosx():

    from syslog import LOG_DAEMON
    from syslog import LOG_PID

    from syslog import LOG_ERR
    from syslog import LOG_WARNING
    from syslog import LOG_INFO
    from syslog import LOG_DEBUG

    from syslog import openlog
    from syslog import syslog

    class SyslogAdaptor:
        def __init__(self):
            openlog("neubot", LOG_DAEMON|LOG_PID)

        def error(self, message):
            syslog(LOG_ERR, message)

        def warning(self, message):
            syslog(LOG_WARNING, message)

        def info(self, message):
            syslog(LOG_INFO, message)

        def debug(self, message):
            syslog(LOG_DEBUG, message)

#
# We save recent messages into a circular queue, together with
# their timestamp, and we do that because we want to return to
# the user also the time when a certain message was generated.
# The purpose of keeping recent messages is NOT to replace the
# traditional logging, but it's because we want to provide to
# our users ALSO this handy information.
#

MAXQUEUE = 100

class Logger:
    def __init__(self, maxqueue):
        self._verbose = False
        self.logger = logging.Logger("neubot.log.Logger")
        self.handler = logging.StreamHandler()
        self.formatter = logging.Formatter("%(message)s")
        self.handler.setFormatter(self.formatter)
        self.logger.addHandler(self.handler)
        self.logger.setLevel(logging.DEBUG)
        self.queue = collections.deque()
        self.message = None
        self.maxqueue = maxqueue
        self._tty = True
        self.prefix = None

    def verbose(self):
        self._verbose = True

    def quiet(self):
        self._verbose = False

    #
    # Some more work -probably- needs to be done in order to
    # redirect logs to a logging file when running under the
    # Windows operating systems family.
    #

    def redirect(self):
#       self.logger.removeHandler(self.handler)
        if ismacosx():
            self.logger = SyslogAdaptor()
            self._tty = False
            return
        self.handler = logging.handlers.SysLogHandler("/dev/log")
        self.handler.setFormatter(self.formatter)
        self.logger.addHandler(self.handler)
        self.logger.setLevel(logging.DEBUG)
        self._tty = False
        self.prefix = "neubot: "

    #
    # In some cases it makes sense to print progress during a
    # long operation, as follows::
    #
    #   Download in progress......... done
    #
    # This makes sense when: (i) the program is not running in
    # verbose mode; (ii) logs are directed to the stderr and the
    # stderr is attached to a TTY.  If the progream is running
    # in verbose mode, there might be many messages between
    # the 'in progress...' and 'done'.  And if the logs are not
    # directed to stderr or stderr is re-directed to a file,
    # then it does not make sense to print progress as well.
    # So, in these cases, the output will look like::
    #
    #   Download in progress...
    #    [here we might have many debug messages]
    #   Download complete.
    #

    def _interactive(self):
        return (not self._verbose and self._tty and isatty(stderr.fileno()))

    def start(self, message):
        if not self._interactive():
            self.info(message + " in progress...")
            self.message = message
        else:
            stderr.write(message + "...")

    def progress(self):
        if self._interactive():
            stderr.write(".")

    def complete(self):
        if not self._interactive():
            self.info(self.message + ": complete")
            self.message = None
        else:
            stderr.write(" done\n")

    #
    # Log functions
    #

    def exception(self):
        content = traceback.format_exc()
        for line in content.splitlines():
            self._log(self.logger.error, line)

    def error(self, message):
        self._log(self.logger.error, message)

    def warning(self, message):
        self._log(self.logger.warning, message)

    def info(self, message):
        self._log(self.logger.info, message)

    def debug(self, message):
        if self._verbose:
            self._log(self.logger.debug, message)

    #
    # XXX We don't want access logs to be saved into the queue, or
    # the client making a request for /logs will cause a new log to
    # be written, and that's not sane.
    #

    def log_access(self, message):
        self._log(self.logger.info, message, False)

    def _log(self, printlog, message, enqueue=True):
        if message[-1] == "\n":
            message = message[:-1]
        if enqueue:
            deque_append(self.queue, self.maxqueue, (time.time(), message))
        if self.prefix:
            message = self.prefix + message
        printlog(message)

    def getlines(self):
        result = []
        for timestamp, line in self.queue:
            result.append((timestamp, line))
        return result

log = Logger(MAXQUEUE)

log_access = log.log_access
verbose = log.verbose
quiet = log.quiet
redirect = log.redirect
exception = log.exception
error = log.error
warning = log.warning
info = log.info
start = log.start
progress = log.progress
complete = log.complete
debug = log.debug
getlines = log.getlines
