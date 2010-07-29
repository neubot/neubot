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

    def verbose(self):
        self._verbose = True

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

    def _log(self, printlog, message):
        if message[-1] == "\n":
            message = message[:-1]
        self.queue.append((time.time(), message))
        printlog(message)

    def getlines(self):
        result = []
        for timestamp, line in self.queue:
            result.append((timestamp, line))
        return result

log = Logger(MAXQUEUE)

verbose = log.verbose
redirect = log.redirect
exception = log.exception
error = log.error
warning = log.warning
info = log.info
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