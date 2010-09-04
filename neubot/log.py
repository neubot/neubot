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
import logging
import time
import traceback

from os import isatty
from sys import stderr

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
        self.queue = collections.deque(maxlen=maxqueue)
        self.message = None
        self._tty = True

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
        self.logger.removeHandler(self.handler)
        self.handler = logging.handlers.SysLogHandler("/dev/log")
        self.handler.setFormatter(self.formatter)
        self.logger.addHandler(self.handler)
        self.logger.setLevel(logging.DEBUG)
        self._tty = False

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
            self.queue.append((time.time(), message))
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

#
# XXX Replace the root logger with log.logger--this is intended as an
# interim measure to use log without converting the existing code base
# from logging.func() to neubot.log.func().
#

def install():
    logging.root = log.logger
    logging.debug = log.debug
    logging.info = log.info
    logging.warning = log.warning
    logging.error = log.error
