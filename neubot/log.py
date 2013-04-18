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

from neubot.config import CONFIG
from neubot.database import DATABASE
from neubot.database import table_log
from neubot.notify import NOTIFIER

from neubot import system
from neubot import utils

def stderr_logger(severity, message):
    if severity not in ('INFO', 'ACCESS'):
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
# Interval in seconds between each invocation of the
# function that compacts the database.
#
INTERVAL_VACUUM = 3600

#
# This is the number of days of logs we keep into
# the database.  Older logs are pruned.
# TODO Allow to configure this.
#
DAYS_AGO = 7

class StreamingLogger(object):

    '''
     Streaming logging feature.

     When a test is invoked from command line, neubot attempts to ask
     the background daemon to run the test.  If that fails, it falls
     back to running the test itself.  When the background daemon runs
     the test, there are a number of advantages.  Including that it
     knows the FQDN of the closest server, and that the test will not
     be run if another test is already in progress.

     In this context, there is the need for a mechanism to pass the
     daemon logs to the client.  Such that the user that invoked the
     command can see the output of the test on the console.

     This need is addressed precisely by the streaming log feature,
     which is implemented by this class.
    '''

    #
    # The streaming feature allows to register a stream such
    # that it receives a copy of all log events.  Effectively
    # allowing for "streaming" of the damons log to interested
    # parties.  As pointed out in the docstring, this is used
    # mainly to implement remote execution of tests.
    #
    # Typically, when a remote test is started, log streaming
    # is automatically set up.  And, when the test is over,
    # the runner automatically schedules for stopping streaming
    # in some seconds.  However, the exact details of how this
    # class is used may change, and you are encouraged to check
    # updater_runner.py implementation for more fresh info.
    #
    # Note that log streaming must pass the client all logs,
    # including DEBUG messages.  And this must work also when
    # the daemon is running in quiet mode.  This means that
    # we cannot rely on the root logger to filter logging
    # events.  Since we must guarantee that all messages will
    # arrive to this class.
    #
    # NOTE The discussion whether passing all the logs along
    # causes slowdowns is open.  So far, I don't think so and
    # don't have observed slowdowns for typical network
    # connections (e.g. 10-100 Mbit/s).  However, that may
    # become a problem for faster connections, so I am
    # deploying this piece of warning.
    #

    def __init__(self):
        self.streams = set()

    def start_streaming(self, stream):
        ''' Attach stream to log messages '''
        self.streams.add(stream)

    def stop_streaming(self):
        ''' Close all attached streams '''
        for stream in self.streams:
            POLLER.close(stream)
        self.streams.clear()

    def log(self, severity, message, args, exc_info):
        ''' Really log a message '''
        try:
            self._log(severity, message, args, exc_info)
        except (SystemExit, KeyboardInterrupt):
            raise
        except:
            pass

    def _log(self, severity, message, args, exc_info):
        ''' Really log a message '''

        # No point in logging empty lines
        if not message:
            return

        if self.streams:

            # Lazy processing
            if args:
                message = message % args
            if exc_info:
                exc_list = traceback.format_exception(exc_info[0],
                                                      exc_info[1],
                                                      exc_info[2])
                message = "%s\n%s\n" % (message, ''.join(exc_list))
                for line in message.split('\n'):
                    self._log(severity, line, None, None)
                return

            message = message.rstrip()

            try:

                logline = "%s %s\r\n" % (severity, message)
                # UTF-8 encoding to avoid supplying unicode to stream.py
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

        self.last_vacuum = 0

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
            self.writeback()

    #
    # We don't want to log into the database when we run
    # the server side or when we run from command line.
    #
    def use_database(self):
        POLLER.sched(INTERVAL, self._maintain_database)
        self._use_database = True

    def redirect(self):
        self.logger = system.get_background_logger()

    def _writeback(self):
        """Really commit pending log records into the database"""

        connection = DATABASE.connection()
        table_log.prune(connection, DAYS_AGO, commit=False)

        for record in self._queue:
            table_log.insert(connection, record, False)
        connection.commit()

        now = utils.ticks()
        if now - self.last_vacuum > INTERVAL_VACUUM:
            connection.execute("VACUUM;")
            self.last_vacuum = now
        connection.commit()

    def writeback(self):
        """Commit pending log records into the database"""

        # At least do not crash
        try:
            self._writeback()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            # TODO write this exception to syslog
            pass

        # Purge the queue in any case
        del self._queue[:]

    def log(self, severity, message, args, exc_info):
        ''' Really log a message '''
        try:
            self._log(severity, message, args, exc_info)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            pass

    def _log(self, severity, message, args, exc_info):
        ''' Really log a message '''

        # No point in logging empty lines
        if not message:
            return

        #
        # Honor verbose.  We cannot leave this choice to the
        # "root" logger because all messages must be passed
        # to the streaming feature.  Hence the "root" logger
        # must always be configured to be vebose.
        #
        if not CONFIG['verbose'] and severity == 'DEBUG':
            return

        # Lazy processing
        if args:
            message = message % args
        if exc_info:
            exc_list = traceback.format_exception(exc_info[0],
                                                  exc_info[1],
                                                  exc_info[2])
            message = "%s\n%s\n" % (message, ''.join(exc_list))
            for line in message.split('\n'):
                self._log(severity, line, None, None)
            return

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
                self.writeback()

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

STREAMING_LOG = StreamingLogger()

class StreamingLogWrapper(logging.Handler):

    """Glue between stdlib logging and StreamingLogger"""

    def emit(self, record):
        msg = record.msg
        args = record.args
        level = record.levelname
        exc_info = record.exc_info
        STREAMING_LOG.log(level, msg, args, exc_info)

ROOT_LOGGER = logging.getLogger()
# Make sure all previously registered handlers go away
ROOT_LOGGER.handlers = []
ROOT_LOGGER.addHandler(LogWrapper())
ROOT_LOGGER.addHandler(StreamingLogWrapper())
ROOT_LOGGER.setLevel(logging.DEBUG)

def set_verbose():
    ''' Make logger verbose '''
    CONFIG['verbose'] = 1

def is_verbose():
    ''' Is the logger verbose? '''
    return CONFIG['verbose']
