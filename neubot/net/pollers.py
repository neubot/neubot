# neubot/net/pollers.py

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
# Poll() and dispatch I/O events (such as "socket readable")
#

import errno
import select
import sys

from neubot.utils import unit_formatter
from neubot.times import ticks
from neubot.times import timestamp
from neubot.utils import SimpleStats
from neubot.utils import Stats
from neubot import log

# Base class for every socket managed by the poller
class Pollable:
    def fileno(self):
        raise NotImplementedError

    def readable(self):
        pass

    def writable(self):
        pass

    def readtimeout(self, now):
        return False

    def writetimeout(self, now):
        return False

    def closed(self, exception=None):
        pass

class PollerTask:
    def __init__(self, delta, func):
        self.time = ticks() + delta
        self.timestamp = timestamp() + int(delta)
        self.func = func

    #
    # Set time to -1 so that sort() move the task at the beginning
    # of the list.  And clear func to allow garbage collection of
    # the referenced object.
    # We need to add timestamp because ticks() might be just the
    # time since neubot started (as happens with Windows).
    #

    def unsched(self):
        self.time = -1
        self.timestamp = -1
        self.func = None

    def resched(self, delta):
        self.time = ticks() + delta
        self.timestamp = timestamp() + int(delta)

    def __del__(self):
        pass

# Interval between each check for timed-out I/O operations
CHECK_TIMEOUT = 10

class Poller:
    def __init__(self, timeout):
        self.timeout = timeout
        self.again = True
        self.printstats = False
        self.readset = {}
        self.writeset = {}
        self.pending = []
        self.tasks = []
        self.sched(CHECK_TIMEOUT, self.check_timeout)
        self.stats = Stats()
        self.sched(1, self._update_stats)

    def __del__(self):
        pass

    def sched(self, delta, func):
        task = PollerTask(delta, func)
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
            log.exception()

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

    def _readable(self, fileno):
        if self.readset.has_key(fileno):
            stream = self.readset[fileno]
            try:
                stream.readable()
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                log.exception()
                self.close(stream)

    def _writable(self, fileno):
        if self.writeset.has_key(fileno):
            stream = self.writeset[fileno]
            try:
                stream.writable()
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                log.exception()
                self.close(stream)

    #
    # Differently from Twisted, we might break out of the loop
    # with registered tasks.  It is probably wiser to behave like
    # Twisted, but this requires to update all the places where
    # loop() is invoked and it might take some time.
    #

    def loop(self):
        while self.again and (self.readset or self.writeset):
            self.update_tasks()
            self.dispatch_events()

    def break_loop(self):
        self.again = False

    #
    # Tests shows that update_tasks() would be slower if we kept tasks
    # sorted in reverse order--yes, with this arrangement it would be
    # faster to delete elements (because it would be just a matter of
    # shrinking the list), but the sort would be slower, and our tests
    # suggest that we loose more with the sort than we gain with the
    # delete.
    #

    def update_tasks(self):
        now = ticks()
        if self.pending:
            for task in self.pending:
                if task.time == -1 or task.func == None:
                    continue
                self.tasks.append(task)
            self.pending = []
        if self.tasks:
            self.tasks.sort(key=lambda task: task.time)
            index = 0
            for task in self.tasks:
                if task.time == -1 or task.func == None:
                    continue
                if task.time > now:
                    break
                try:
                    task.func()
                except (KeyboardInterrupt, SystemExit):
                    raise
                except:
                    log.exception()
                index = index + 1
            del self.tasks[:index]

    def dispatch_events(self):
        if self.readset or self.writeset:
            try:
                res = select.select(self.readset.keys(), self.writeset.keys(),
                 [], self.timeout)
            except select.error, (code, reason):
                if code != errno.EINTR:
                    log.exception()
                    raise
            else:
                for fileno in res[0]:
                    self._readable(fileno)
                for fileno in res[1]:
                    self._writable(fileno)

    def check_timeout(self):
        self.sched(CHECK_TIMEOUT, self.check_timeout)
        if self.readset or self.writeset:
            now = ticks()
            x = self.readset.values()
            for stream in x:
                if stream.readtimeout(now):
                    self.close(stream)
            x = self.writeset.values()
            for stream in x:
                if stream.writetimeout(now):
                    self.close(stream)

    def disable_stats(self):
        if self.printstats:
            sys.stdout.write("\n")
        self.printstats = False

    def enable_stats(self):
        self.printstats = True

    def _update_stats(self):
        self.sched(1, self._update_stats)
        if self.printstats:
            # send
            self.stats.send.end()
            send = self.stats.send.speed()
            self.stats.send.begin()
            # recv
            self.stats.recv.end()
            recv = self.stats.recv.speed()
            self.stats.recv.begin()
            # print
            stats = "\r    send: %s | recv: %s" % (
             unit_formatter(send, unit="B/s"),
             unit_formatter(recv, unit="B/s"))
            if len(stats) < 80:
                stats += " " * (80 - len(stats))
            sys.stdout.write(stats)
            sys.stdout.flush()

poller = Poller(1)

loop = poller.loop
sched = poller.sched
disable_stats = poller.disable_stats
enable_stats = poller.enable_stats
break_loop = poller.break_loop
