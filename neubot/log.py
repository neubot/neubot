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
import sys
import time
import traceback

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.compat import deque_append
from neubot.compat import json
from neubot.utils import timestamp
from neubot import system


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

    """Logging object.  Usually there should be just one instance
       of this class, accessible with the default logging object
       LOGGER.  We keep recent logs in a queue in order to implement
       the /api/log API."""

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
        self.logger = system.BackgroundLogger()
        system.redirect_to_dev_null()
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
            if not self.message:
                self.message = "???"
            self.info(self.message + ": complete")
            self.message = None
        else:
            sys.stderr.write(" done\n")

    # Log functions

    def exception(self):
        for line in traceback.format_exc().split("\n"):
            self._log(self.logger.error, "ERROR", line)

    def error(self, message):
        self._log(self.logger.error, "ERROR", message)

    def warning(self, message):
        self._log(self.logger.warning, "WARNING", message)

    def info(self, message):
        self._log(self.logger.info, "INFO", message)

    def debug(self, message):
        if self.noisy:
            self._log(self.logger.debug, "DEBUG", message)

    def log_access(self, message):
        #
        # CAVEAT Currently Neubot do not update logs "in real
        # time" using AJAX.  If it did we would run in trouble
        # because each request for /api/log would generate a
        # new access log record.  A new access log record will
        # cause a new "logwritten" event.  And the result is
        # something like a Comet storm.
        #
        self._log(self.logger.info, "INFO", message)

    def _log(self, printlog, severity, message):
        message = message.rstrip()
        deque_append(self.queue, self.maxqueue, (timestamp(),severity,message))
        printlog(message)

    # Marshal

    def serialize(self):
        return map(None, self.queue)


MAXQUEUE = 100
LOG = Logger(MAXQUEUE)

if __name__ == "__main__":
    LOG.verbose()

    LOG.error("testing neubot logger -- This is an error message")
    LOG.warning("testing neubot logger -- This is an warning message")
    LOG.info("testing neubot logger -- This is an info message")
    LOG.debug("testing neubot logger -- This is a debug message")
    print json.dumps(LOG.serialize())

    LOG.redirect()

    LOG.error("testing neubot logger -- This is an error message")
    LOG.warning("testing neubot logger -- This is an warning message")
    LOG.info("testing neubot logger -- This is an info message")
    LOG.debug("testing neubot logger -- This is a debug message")
