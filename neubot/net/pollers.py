# neubot/net/pollers.py
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
# Poll() and dispatch I/O events (such as "socket readable")
#

import errno
import logging
import select
import time

from neubot.utils import prettyprint_exception
from neubot.utils import ticks

import neubot

# Base class for every socket managed by the poller
class Pollable:
    def closing(self):
        pass

    def fileno(self):
        raise Exception("You must override this method")

    def readable(self):
        pass

    def writable(self):
        pass

    def readtimeout(self, now):
        return False

    def writetimeout(self, now):
        return False

class PollerTask:
    def __init__(self, time, func, periodic, delta):
        self.time = time
        self.func = func
        self.periodic = periodic
        self.delta = delta

class Poller:
    def __init__(self, timeout, get_ticks, notify_except):
        self.timeout = timeout
        self.get_ticks = get_ticks
        self.notify_except = notify_except
        self.readset = {}
        self.writeset = {}
        self.added = set()
        self.registered = {}
        self.tasks = []
        self.sched(self.timeout, self.check_timeout)

    def __del__(self):
        pass

    #
    # Unsched() does not remove a task, but it just marks it as "dead",
    # and this means that (a) it sets its func member to None, and (b)
    # its time to -1.  The (a) step breks the reference from the task
    # to the object that registered the task (and so the object could
    # possibly be collected).  The (b) step causes the dead task to be
    # moved at the beginning of the list, and we do that because we
    # don't want a dead task to linger in the list for some time (in
    # other words we optimize for memory rather than for speed).
    #

    def sched(self, delta, func, periodic=False):
        if self.registered.has_key(func):
            task = self.registered[func]
            task.time = self.get_ticks() + delta
            task.periodic = periodic
        else:
            self.added.add((delta, func, periodic))

    def unsched(self, delta, func):
        if self.registered.has_key(func):
            task = self.registered[func]
            task.func = None
            task.time = -1
            del self.registered[func]
        else:
            # Not sure whether this could happen
            entry = (delta, func)
            if entry in self.added:
                self.added.remove(entry)

    #
    # BEGIN deprecated functions
    # Use the sched() / unsched() interface instead

    def register_periodic(self, periodic):
        neubot.log.debug("register_periodic() is deprecated")
        self.sched(self.timeout, periodic, True)

    def unregister_periodic(self, periodic):
        neubot.log.debug("unregister_periodic() is deprecated")
        self.unsched(self.timeout, periodic)

    def register_func(self, func):
        neubot.log.debug("register_func() is deprecated")
        self.sched(0, func)

    # END deprecated functions
    #

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
        stream.closing()

    #
    # We are very careful when accessing readset and writeset because
    # we cannot be sure that there is an entry for fileno even if there
    # was an entry when we started select().  Consider the following
    # case: We have a stream that is both readable and writable and so
    # when select() returns we have the stream fileno both in the res[0]
    # (readable) and in the res[1] (writable) sets.  Then, we iterate
    # over res[0], we map each fileno to its stream using readset, and
    # we invoke each stream's readable() method.  When we invoke the
    # readable() method of our stream, there in an exception, and such
    # exception is caught, self.close(stream) is invoked, and eventually
    # our stream is garbage collected.  But its fileno still is in the
    # res[1] set, because select() found our stream writable!  So, when
    # we loop over res[1] (writable filenos) we eventually hit the fileno
    # of our stream, even if such stream has already been closed.
    # Hence, the self.writeset.has_key() check [The check in _readable()
    # is needless, but we keep it in place for robustness and for
    # simmetry with _writable().]  Hope this explains the couple of XXX
    # below.
    #

    def _readable(self, fileno):
        if self.readset.has_key(fileno):                                # XXX
            stream = self.readset[fileno]
            stream.readable()

    def _writable(self, fileno):
        if self.writeset.has_key(fileno):                               # XXX
            stream = self.writeset[fileno]
            stream.writable()

    #
    # Welcome to the core loop.
    #
    # Probably the core loop was faster when it was just
    # one single complex function, but written in this
    # way it is simpler to deal with reference counting
    # issues.
    # When iterating overs sets & co. we make a (shallow)
    # copy of each set so that it is possible to modify
    # the original during the iteration.  Or, as happens
    # with run-once functions, after the copy, we clear
    # the original.
    #

    def loop(self):
        while self.added or self.tasks or self.readset or self.writeset:
            self.update_tasks()
            self.dispatch_events()

    def dispatch(self):
        if self.added or self.tasks or self.readset or self.writeset:
            self.update_tasks()
            self.dispatch_events()

    #
    # Tests shows that update_tasks() would be slower if we kept tasks
    # sorted in reverse order--yes, with this arrangement it would be
    # faster to delete elements (because it would be just a matter of
    # shrinking the list), but the sort would be slower, and, our tests
    # suggest that we loose more with the sort than we gain with the
    # delete.
    #

    def update_tasks(self):
        now = self.get_ticks()
        if self.added:
            for delta, func, periodic in self.added:
                task = PollerTask(now + delta, func, periodic, delta)
                self.tasks.append(task)
                self.registered[func] = task
            self.added.clear()
        if self.tasks:
            self.tasks.sort(key=lambda task: task.time)
            index = 0
            for task in self.tasks:
                if task.time > 0:
                    if task.time > now:
                        break
                    if task.func:                       # redundant
                        del self.registered[task.func]
                        if task.periodic:
                            task.func(now)
                            self.sched(task.delta, task.func, True)
                        else:
                            task.func()
                index = index + 1
            del self.tasks[:index]

    def dispatch_events(self):
        if self.readset or self.writeset:
            try:
                res = select.select(self.readset.keys(),
                    self.writeset.keys(), [], self.timeout)
            except select.error, (code, reason):
                if code != errno.EINTR:
                    self.notify_except()
                    raise
            else:
                for fileno in res[0]:
                    self._readable(fileno)
                for fileno in res[1]:
                    self._writable(fileno)

    def check_timeout(self):
        if self.readset or self.writeset:
            self.sched(self.timeout, self.check_timeout)
            now = self.get_ticks()
            x = self.readset.values()
            for stream in x:
                if stream.readtimeout(now):
                    self.close(stream)
            x = self.writeset.values()
            for stream in x:
                if stream.writetimeout(now):
                    self.close(stream)

def create_poller(timeout=1, get_ticks=ticks,
        notify_except=prettyprint_exception):
    return Poller(timeout, get_ticks, notify_except)

poller = create_poller()
dispatch = poller.dispatch
loop = poller.loop
register_periodic = poller.register_periodic
sched = poller.sched
unsched = poller.unsched
