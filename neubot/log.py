# neubot/log.py

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
# Wrapper for logging
#

import collections
import logging.handlers
import time
import traceback
import os
import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.compat import deque_append
from neubot.unix import *
from neubot.win32 import *

#
# XXX neubot/utils.py depends on this file so we must roll out our
# own version of timestamp().  It could also make sense to move here
# the definition of timestamp and pull from this file in utils.py.
#

timestamp = lambda: int(time.time())

#
# We save recent messages into a circular queue, together with
# their timestamp, and we do that because we want to return to
# the user also the time when a certain message was generated.
# The purpose of keeping recent messages is NOT to replace the
# traditional logging, but it's because we want to provide to
# our users ALSO this handy information.
#

MAXQUEUE = 100

class InteractiveLogger(object):

        """Log messages on the standard error.  This is the simplest
           logger one can think and is the one we use at startup."""

        def error(self, message):
            sys.stderr.write(message + "\n")

        def warning(self, message):
            sys.stderr.write(message + "\n")

        def info(self, message):
            sys.stderr.write(message + "\n")

        def debug(self, message):
            sys.stderr.write(message + "\n")

class Logger(object):

    def __init__(self, maxqueue):
        self.logger = InteractiveLogger()

        self.queue = collections.deque()
        self.maxqueue = maxqueue

        self.interactive = True
        self.noisy = False

        self.message = None

    def verbose(self):
        self.noisy = True

    def quiet(self):
        self.noisy = False

    def redirect(self):
        self.logger = BackgroundLogger()
        self.interactive = False

    #
    # In some cases it makes sense to print progress during a
    # long operation, as follows::
    #
    #   Download in progress......... done
    #
    # This makes sense when: (i) the program is not running in
    # verbose mode; (ii) logs are directed to the stderr.
    # If the program is running in verbose mode, there might
    # be many messages between the 'in progress...' and 'done'.
    # And if the logs are not directed to stderr then it does
    # not make sense to print progress as well.
    # So, in these cases, the output will look like::
    #
    #   Download in progress...
    #    [here we might have many debug messages]
    #   Download complete.
    #

    def start(self, message):
        if self.noisy or not self.interactive:
            self.info(message + " in progress...")
            self.message = message
        else:
            sys.stderr.write(message + "...")

    def progress(self):
        if not self.noisy and self.interactive:
            sys.stderr.write(".")

    def complete(self):
        if self.noisy or not self.interactive:
            self.info(self.message + ": complete")
            self.message = None
        else:
            sys.stderr.write(" done\n")

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
        if self.noisy:
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
            deque_append(self.queue, self.maxqueue, (timestamp(), message))
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

def main(args):
    verbose()
    error("testing neubot logger -- This is an error message")
    warning("testing neubot logger -- This is an warning message")
    info("testing neubot logger -- This is an info message")
    debug("testing neubot logger -- This is a debug message")
    redirect()
    error("testing neubot logger -- This is an error message")
    warning("testing neubot logger -- This is an warning message")
    info("testing neubot logger -- This is an info message")
    debug("testing neubot logger -- This is a debug message")

if __name__ == "__main__":
    main(sys.argv)
