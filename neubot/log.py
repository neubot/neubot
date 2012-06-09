# neubot/log.py

#
# Copyright (c) 2010-2011 Simone Basso <bassosimone@gmail.com>,
#  NEXA Center for Internet & Society at Politecnico di Torino
# Copyright (c) 2012 Marco Scopesi <marco.scopesi@gmail.com>
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

import sys
import logging
import traceback

from neubot.net.poller import POLLER

from neubot.database import DATABASE
from neubot.database import table_log
from neubot.notify import NOTIFIER

from neubot import system
from neubot import utils

def stderr_logger(severity, message):
    if severity != 'INFO':
        sys.stderr.write('%s: %s\n' % (severity, message))
    else:
        sys.stderr.write('%s\n' % message)

#
# We commit every NOCOMMIT log messages or when we see
# a WARNING or ERROR message (whichever of the two comes
# first).
#
NOCOMMIT = 32

#
# Interval in seconds between each invocation of the
# function that takes care of the logs saved into the
# database.
#
INTERVAL = 120

#
# This is the number of days of logs we keep into
# the database.  Older logs are pruned.
# TODO Allow to configure this.
#
DAYS_AGO = 7

class StreamLogger(object):

    ''' Stream logging object '''

    def __init__(self):
        self.streams = set()

    def start_streaming(self, stream):
        ''' Attach stream to log messages '''
        self.streams.add(stream)

    def stop_streaming(self):
        ''' Close all attached streams '''
        for stream in self.streams:
            stream.poller.close(stream)
        self.streams.clear()

    def log(self, severity, message, args, exc_info):
        ''' Really log a message (without any *magic) '''

        # No point in logging empty lines
        if not message:
            return

        #
        # Streaming allows consumers to register with the log
        # object and follow the events that happen during a
        # test as if they were running the test in their local
        # context.  When the test is done, the runner of the
        # test will automatically disconnected all the attached
        # streams.
        # Log streaming makes this function less efficient
        # because lazy processing of log records can't be
        # performed.  We must pass the client all the logs
        # and it will decide whether to be verbose.
        # Err, of course passing ACCESS logs down the stream
        # is pointless for a client that wants to follow a
        # remote test.
        #
        if self.streams:
            # "Lazy" processing
            if args:
                message = message % args
                args = ()
            if exc_info:
                message = "%s: %s\n" % (message, str(exc_info[1]))
                # Ensure we do not accidentaly keep the exception alive
                exc_info = None
            message = message.rstrip()
            try:
                if severity != 'ACCESS':
                    logline = "%s %s\r\n" % (severity, message)
                    logline = logline.encode("utf-8")
                    for stream in self.streams:
                        stream.start_send(logline)
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                pass


class Logger(object):

    """Logging object.  Usually there should be just one instance
       of this class, accessible with the default logging object
       LOG.  We keep recent logs in the database in order to implement
       the /api/log API."""

    def __init__(self):
        self.logger = stderr_logger
        self.message = None
        self.ticks = 0

        self._nocommit = NOCOMMIT
        self._use_database = False
        self._queue = []

    #
    # Better not to touch the database when a test is in
    # progress, i.e. "testdone" is subscribed.
    # Maintenance consists mainly of removing old logs and
    # is mandatory because we don't want the database to grow
    # without control.
    #
    def _maintain_database(self):

        POLLER.sched(INTERVAL, self._maintain_database)

        if (self._use_database and not NOTIFIER.is_subscribed("testdone")):
            self._writeback()

    #
    # We don't want to log into the database when we run
    # the server side or when we run from command line.
    #
    def use_database(self):
        POLLER.sched(INTERVAL, self._maintain_database)
        self._use_database = True

    def redirect(self):
        self.logger = system.get_background_logger()
        system.redirect_to_dev_null()

    def __writeback(self):
        """Really commit pending log records into the database"""

        connection = DATABASE.connection()
        table_log.prune(connection, DAYS_AGO, commit=False)

        for record in self._queue:
            table_log.insert(connection, record, False)
        connection.commit()

        connection.execute("VACUUM;")
        connection.commit()

    def _writeback(self):
        """Commit pending log records into the database"""

        # At least do not crash
        try:
            self.__writeback()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            # TODO write this exception to syslog
            pass

        # Purge the queue in any case
        del self._queue[:]

    def log(self, severity, message, args, exc_info):
        ''' Really log a message (without any *magic) '''

        # No point in logging empty lines
        if not message:
            return

        # Lazy processing
        if args:
            message = message % args
            args = ()
        if exc_info:
            message = "%s: %s\n" % (message, str(exc_info[1]))
            # Ensure we do not accidentaly keep the exception alive
            exc_info = None
        message = message.rstrip()

        # Write log into the database
        if self._use_database and severity != "ACCESS":
            record = {
                      "timestamp": utils.timestamp(),
                      "severity": severity,
                      "message": message,
                     }

            #
            # We don't need to commit INFO and DEBUG
            # records: it's OK to see those with some
            # delay.  While we want to see immediately
            # WARNING and ERROR records.
            # TODO We need to commit the database on
            # sys.exit() and signals etc.  (This is
            # more a database problem that a problem
            # of this file.)
            #
            if severity in ("INFO", "DEBUG"):
                commit = False

                # Do we need to commit now?
                self._nocommit = self._nocommit -1
                if self._nocommit <= 0:
                    self._nocommit = NOCOMMIT
                    commit = True

            else:
                # Must commit now
                self._nocommit = NOCOMMIT
                commit = True

            self._queue.append(record)
            if commit:
                self._writeback()

        # Write to the current logger object
        self.logger(severity, message)

    # Marshal

    def listify(self):
        if self._use_database:
            lst = table_log.listify(DATABASE.connection())
            lst.extend(self._queue)
            return lst
        else:
            return []

def oops(message="", func=None):
    if not func:
        func = logging.error
    if message:
        func("OOPS: " + message + " (traceback follows)")
    for line in traceback.format_stack()[:-1]:
        func(line)

LOG = Logger()

class LogWrapper(logging.Handler):

    """Wrapper for stdlib logging."""

    def emit(self, record):
        msg = record.msg
        args = record.args
        level = record.levelname
        exc_info = record.exc_info
        LOG.log(level, msg, args, exc_info)

class AccessLogWrapper(logging.Handler):

    """Wrapper for stdlib logging."""

    def emit(self, record):
        msg = record.msg
        args = record.args
        exc_info = record.exc_info
        LOG.log('ACCESS', msg, args, exc_info)

STREAM_LOG = StreamLogger()

class StreamLogWrapper(logging.Handler):

    """Wrapper between stdlib logging and StreamLogger"""

    def emit(self, record):
        msg = record.msg
        args = record.args
        level = record.levelname
        exc_info = record.exc_info
        STREAM_LOG.log(level, msg, args, exc_info)

ROOT_LOGGER = logging.getLogger()
ROOT_LOGGER.handlers = []
ROOT_LOGGER.addHandler(LogWrapper())
ROOT_LOGGER.addHandler(StreamLogWrapper(level=logging.DEBUG))
ROOT_LOGGER.setLevel(logging.INFO)
# Create 'access' logger
ACCESS_LOGGER = logging.getLogger('access')
ACCESS_LOGGER.setLevel(logging.INFO)
ACCESS_LOGGER.addHandler(AccessLogWrapper())
# Avoid passing log messages to the ROOT logger
ACCESS_LOGGER.propagate = False
