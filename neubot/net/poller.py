# neubot/net/poller.py

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

import errno
import select
import time

from neubot.utils import ticks
from neubot.utils import timestamp
from neubot.log import LOG

# Interval between each check for timed-out I/O operations
CHECK_TIMEOUT = 10

class Pollable(object):

    def __init__(self):
        self.created = ticks()
        self.watchdog = -1

    def fileno(self):
        raise NotImplementedError

    def handle_readable(self):
        pass

    def handle_writable(self):
        pass

    def readtimeout(self, now):
        return False

    def writetimeout(self, now):
        return False

    def closed(self, exception=None):
        pass

class Task(object):

    #
    # We need to add timestamp because ticks() might be just the
    # time since neubot started (as happens with Windows).
    #
    def __init__(self, delta, func, *args, **kwargs):
        self.time = ticks() + delta
        self.timestamp = timestamp() + int(delta)
        self.func = func
        self.args = args
        self.kwargs = kwargs

    #
    # Set time to -1 so that sort() move the task at the beginning
    # of the list.  And clear func to allow garbage collection of
    # the referenced object.
    #
    def unsched(self):
        self.time = -1
        self.timestamp = -1
        self.func = None
        self.args = None
        self.kwargs = None

    def resched(self, delta, *args, **kwargs):
        self.time = ticks() + delta
        self.timestamp = timestamp() + int(delta)
        if args:
            self.args = args
        if kwargs:
            self.kwargs = kwargs

    # TODO We should represent args and kwargs as well
    def __repr__(self):
        return ("Task: time=%(time)f timestamp=%(timestamp)d func=%(func)s" %
          self.__dict__)

class Poller(object):

    def __init__(self, select_timeout):
        self.select_timeout = select_timeout
        self.again = True
        self.readset = {}
        self.writeset = {}
        self.pending = []
        self.tasks = []
        self.sched(CHECK_TIMEOUT, self.check_timeout)

    def sched(self, delta, func, *args, **kwargs):
        task = Task(delta, func, *args, **kwargs)
        self.pending.append(task)
        return task

    def set_readable(self, stream):
        self.readset[stream.fileno()] = stream

    def set_writable(self, stream):
        self.writeset[stream.fileno()] = stream

    def unset_readable(self, stream):
        fileno = stream.fileno()
        if self.readset.has_key(fileno):
            del self.readset[fileno]

    def unset_writable(self, stream):
        fileno = stream.fileno()
        if self.writeset.has_key(fileno):
            del self.writeset[fileno]

    def close(self, stream):
        self.unset_readable(stream)
        self.unset_writable(stream)
        try:
            stream.closed()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            LOG.exception()

    #
    # We are very careful when accessing readset and writeset because
    # it's possible that the fileno makes reference to a stream that
    # does not exist anymore.  Consider the following example: There is
    # a stream that is both readable and writable, and so its fileno
    # is both in res[0] and res[1].  But, when we invoke the stream's
    # readable() callback there is a protocol violation and so the
    # high-level code invokes close(), and the stream is closed, and
    # hence removed from readset and writeset.  And then the stream
    # does not exist anymore, but its fileno still is in res[1].
    #

    def _call_handle_readable(self, fileno):
        if self.readset.has_key(fileno):
            stream = self.readset[fileno]
            try:
                stream.handle_readable()
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                LOG.exception()
                self.close(stream)

    def _call_handle_writable(self, fileno):
        if self.writeset.has_key(fileno):
            stream = self.writeset[fileno]
            try:
                stream.handle_writable()
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                LOG.exception()
                self.close(stream)

    #
    # Has optional arguments because often we need to schedule
    # this function after a given time.
    #
    def break_loop(self, *args, **kwargs):
        self.again = False

    #
    # Differently from Twisted, we might break out of the loop
    # with registered tasks.  It is probably wiser to behave like
    # Twisted, but this requires to update all the places where
    # loop() is invoked and it might take some time.
    #

    def loop(self):
        while self.again and (self.readset or self.writeset):
            self._loop_once()

    #
    # Tests shows that updating tasks would be slower if we kept tasks
    # sorted in reverse order--yes, with this arrangement it would be
    # faster to delete elements (because it would be just a matter of
    # shrinking the list), but the sort would be slower, and our tests
    # suggest that we loose more with the sort than we gain with the
    # delete.
    #
    def _loop_once(self):

        now = ticks()

        # Add pending tasks
        if self.pending:
            for task in self.pending:

                # Unscheduled!
                if task.time == -1 or task.func == None:
                    continue

                self.tasks.append(task)
            self.pending = []

        # Process expired tasks
        if self.tasks:

            #
            # Move new tasks to the proper place and move
            # unscheduled tasks at the beginning (since they
            # have task.time == -1).
            #
            self.tasks.sort(key=lambda task: task.time)

            # Run expired tasks
            index = 0
            for task in self.tasks:
                if task.time - now > 1:
                    break
                index = index + 1

                # Unscheduled!
                if task.time == -1 or task.func == None:
                    continue

                try:
                    task.func(task.args, task.kwargs)
                except (KeyboardInterrupt, SystemExit):
                    raise
                except:
                    LOG.exception()

            # Get rid of expired tasks
            del self.tasks[:index]

        #
        # Calculate select() timeout now that all
        # the tasks are in a good state, i.e. no pending
        # and no unscheduled tasks around.
        #
        if not self.tasks:
            timeout = self.select_timeout
        else:
            timeout = self.tasks[0].time - now
            if timeout < 0.1:
                timeout = 0

        # Monitor streams readability/writability
        if self.readset or self.writeset:

            # Get list of readable/writable streams
            try:
                res = select.select(self.readset.keys(), self.writeset.keys(),
                 [], timeout)
            except select.error, (code, reason):
                if code != errno.EINTR:
                    LOG.exception()
                    raise

                else:
                    # Take care of EINTR
                    return

            # No error?  Fire readable and writable events
            for fileno in res[0]:
                self._call_handle_readable(fileno)
            for fileno in res[1]:
                self._call_handle_writable(fileno)

        #
        # No I/O pending?  So let's just wait for the
        # next task to be ready to be fired.
        #
        elif timeout > 0:
            time.sleep(timeout)

    def check_timeout(self, *args, **kwargs):
        self.sched(CHECK_TIMEOUT, self.check_timeout)
        if self.readset or self.writeset:
            now = ticks()
            stale = set()

            x = self.readset.values()
            for stream in x:
                if stream.readtimeout(now):
                    LOG.warning("%s: read timeout" % repr(stream))
                    stale.add(stream)
                elif (stream.watchdog > 0 and
                   now - stream.created > stream.watchdog):
                    LOG.warning("%s: watchdog timeout" % repr(stream))
                    stale.add(stream)

            x = self.writeset.values()
            for stream in x:
                if stream.writetimeout(now):
                    LOG.warning("%s: write timeout" % repr(stream))
                    stale.add(stream)
                elif (stream.watchdog > 0 and
                   now - stream.created > stream.watchdog):
                    LOG.warning("%s: watchdog timeout" % repr(stream))
                    stale.add(stream)

            for stream in stale:
                self.close(stream)

    def snap(self, d):
        d['poller'] = {"pending": self.pending, "tasks": self.tasks,
          "readset": self.readset, "writeset": self.writeset}

POLLER = Poller(1)
