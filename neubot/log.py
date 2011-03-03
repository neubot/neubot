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
import time
import traceback
import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.compat import deque_append
from neubot.compat import json
from neubot.times import timestamp

# fetch BackgroundLogger from either unix or win32
from neubot.unix import *
from neubot.win32 import *

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

    """Main wrapper for logging.  The queue allows us to export
       recent logs via /api/logs."""

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
            if not self.message:
                self.message = "???"
            self.info(self.message + ": complete")
            self.message = None
        else:
            sys.stderr.write(" done\n")

    # Log functions

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

    def log_access(self, message):
        # Note enqueue MUST be False to avoid /api/logs comet storm
        self._log(self.logger.info, message, False)

    def _log(self, printlog, message, enqueue=True):
        if message[-1] == "\n":
            message = message[:-1]
        if enqueue:
            deque_append(self.queue, self.maxqueue, (timestamp(), message))
        printlog(message)

    # Marshal

    def __str__(self):
        results = []
        for tstamp, message in self.queue:
            dictionary = {}
            dictionary["timestamp"] = tstamp
            dictionary["message"] = message
            results.append(dictionary)
        try:
            data = json.dumps(results, ensure_ascii=True)
        except (UnicodeEncodeError, UnicodeDecodeError):
            data = ""
        return data

MAXQUEUE = 100
LOG = Logger(MAXQUEUE)
__all__ = [ "LOG" ]

### DEPRECATED ###
#

log = LOG

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

                 #
### DEPRECATED ###

def main(args):
    LOG.verbose()
    LOG.error("testing neubot logger -- This is an error message")
    LOG.warning("testing neubot logger -- This is an warning message")
    LOG.info("testing neubot logger -- This is an info message")
    LOG.debug("testing neubot logger -- This is a debug message")
    LOG.redirect()
    LOG.error("testing neubot logger -- This is an error message")
    LOG.warning("testing neubot logger -- This is an warning message")
    LOG.info("testing neubot logger -- This is an info message")
    LOG.debug("testing neubot logger -- This is a debug message")
    print str(LOG)

if __name__ == "__main__":
    main(sys.argv)
