# neubot/poller_libneubot.py

#
# Copyright (c) 2013
#     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
#     and Simone Basso <bassosimone@gmail.com>.
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
# Python3-ready: yes
# pylint: disable = C0111, R0923
#

import sys

sys.path.insert(0, "/usr/local/share/libneubot")  # XXX

from libneubot import LIBNEUBOT
from libneubot import NEUBOT_POLLABLE_CALLBACK
from libneubot import NEUBOT_POLLER_CALLBACK

from neubot.poller_interface import PollableInterface
from neubot.poller_interface import PollerInterface

def _handle_read(pyobject):
    pyobject.handle_read()

HANDLE_READ = NEUBOT_POLLABLE_CALLBACK(_handle_read)

def _handle_write(pyobject):
    pyobject.handle_write()

HANDLE_WRITE = NEUBOT_POLLABLE_CALLBACK(_handle_write)

def _handle_close(pyobject):
    pyobject.handle_close()

HANDLE_CLOSE = NEUBOT_POLLABLE_CALLBACK(_handle_close)

class PollableLibneubot(PollableInterface):

    def __init__(self, poller):
        PollableInterface.__init__(self, poller)
        self._handle = LIBNEUBOT.NeubotPollable_construct(
          poller.get_handle_(), HANDLE_READ, HANDLE_WRITE, HANDLE_CLOSE, self)
        poller.register_pollable_(self)  # XXX

    def attach(self, filenum):
        print "attach", self._handle, filenum
        return LIBNEUBOT.NeubotPollable_attach(self._handle, filenum)

    def detach(self):
        LIBNEUBOT.NeubotPollable_detach(self._handle)

    def fileno(self):
        return LIBNEUBOT.NeubotPollable_fileno(self._handle)

    def set_readable(self):
        print "set_readable", self._handle
        return LIBNEUBOT.NeubotPollable_set_readable(self._handle)

    def unset_readable(self):
        return LIBNEUBOT.NeubotPollable_unset_readable(self._handle)

    def handle_read(self):
        pass

    def set_writable(self):
        return LIBNEUBOT.NeubotPollable_set_writable(self._handle)

    def unset_writable(self):
        return LIBNEUBOT.NeubotPollable_unset_writable(self._handle)

    def handle_write(self):
        pass

    def set_timeout(self, delta):
        LIBNEUBOT.NeubotPollable_set_timeout(self._handle, delta)

    def clear_timeout(self):
        LIBNEUBOT.NeubotPollable_clear_timeout(self._handle)

    def handle_periodic(self):
        pass  # XXX

    def close(self):
        LIBNEUBOT.NeubotPollable_close(self._handle)

    def handle_close(self):
        pass

def _handle_callback(pyobject):
    poller, pytuple = pyobject
    poller.handle_callback_(pytuple)

HANDLE_CALLBACK = NEUBOT_POLLER_CALLBACK(_handle_callback)

class PollerLibneubot(PollerInterface):

    def __init__(self):
        PollerInterface.__init__(self)
        self._handle = LIBNEUBOT.NeubotPoller_construct()
        self._args = {}
        self._pollables = set()

    def sched(self, delta, function, argument):
        pytuple = function, argument
        self._args[pytuple] = 1
        pyobject = self, pytuple
        LIBNEUBOT.NeubotPoller_sched(self._handle, delta,
          HANDLE_CALLBACK, pyobject)

    def _handle_callback(self, pytuple):
        del self._args[pytuple]
        function, argument = pytuple
        function(argument)

    def loop(self):
        LIBNEUBOT.NeubotPoller_loop(self._handle)

    def break_loop(self):
        LIBNEUBOT.NeubotPoller_break_loop(self._handle)

    def get_handle_(self):
        return self._handle

    def register_pollable_(self, pollable):
        self._pollables.add(pollable)

    def unregister_pollable_(self, pollable):
        self._pollables.remove(pollable)
