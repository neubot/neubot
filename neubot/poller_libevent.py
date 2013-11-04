# neubot/poller_libevent.py

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
# pylint: disable=C0111
#

import ctypes
import logging
import math
import signal

from neubot.poller_interface import PollableInterface
from neubot.poller_interface import PollerInterface

from neubot import utils

EV_TIMEOUT = 0x01
EV_READ = 0x02
EV_WRITE = 0x04
EV_SIGNAL = 0x08
EV_PERSIST = 0x10

class Timeval(ctypes.Structure):  # XXX nonportable
    # pylint: disable=R0903
    _fields_ = [
                ("tv_sec", ctypes.c_long),
                ("tv_usec", ctypes.c_long),
               ]

CALLBACK_T = ctypes.CFUNCTYPE(None, ctypes.c_int,
    ctypes.c_short, ctypes.c_void_p)

def _handle_pollable_event(fileno, event, opaque):
    # pylint: disable=W0702,W0613

    pyobject = ctypes.cast(opaque, ctypes.py_object).value

    try:
        if event & EV_READ:
            pyobject.handle_read()
        elif event & EV_WRITE:
            pyobject.handle_write()
        else:
            raise RuntimeError("unexpected event")
    except:
        logging.warning("unhandled exception", exc_info=1)
        pyobject.close()

def _handle_poller_event(fileno, event, opaque):
    # pylint: disable=W0702,W0613

    pyobject = ctypes.cast(opaque, ctypes.py_object).value

    if event & EV_SIGNAL:
        pyobject.break_loop()
        return

    if event & EV_TIMEOUT:
        function, argument, poller = pyobject
        event, timeo = poller.arguments.pop(pyobject)
        poller.event_del_(event)
        function(argument)
        return

_HANDLE_POLLABLE_EVENT = CALLBACK_T(_handle_pollable_event)
_HANDLE_POLLER_EVENT = CALLBACK_T(_handle_poller_event)

class PollableLibevent(PollableInterface):

    # TODO: make sure that event_new_() does not return NULL
    # TODO: set a default timeout of 300 seconds
    # TODO: make sure that we close the libevent's events

    def __init__(self, poller):
        PollableInterface.__init__(self, poller)
        self.poller = poller
        self.filenum = -1
        self.evread = None
        self.evwrite = None
        self.timeo = -1

    def attach(self, filenum):
        self.filenum = filenum
        self.evread = self.poller.event_new_(self.filenum,
                        EV_READ|EV_PERSIST, self)
        self.evwrite = self.poller.event_new_(self.filenum,
                         EV_WRITE|EV_PERSIST, self)
        self.poller.register_pollable_(self)

    def detach(self):
        if self.filenum < 0:
            return
        self.poller.event_free_(self.evwrite)
        self.poller.event_free_(self.evread)
        self.poller.unregister_pollable_(self)
        self.filenum = -1

    def fileno(self):
        return self.filenum

    def set_readable(self):
        self.poller.event_add_(self.evread, None)

    def unset_readable(self):
        self.poller.event_del_(self.evread)

    def set_writable(self):
        self.poller.event_add_(self.evwrite, None)

    def unset_writable(self):
        self.poller.event_del_(self.evwrite)

    def set_timeout(self, delta):
        self.timeo = utils.ticks() + delta

    def clear_timeout(self):
        self.timeo = -1

    def handle_periodic(self):
        if self.timeo >= 0 and utils.ticks() > self.timeo:
            logging.warning("poller_libevent: Watchdog timeout")
            self.close()

    def close(self):
        self.detach()
        self.handle_close()

    def handle_close(self):
        pass

class PollerLibevent(PollerInterface):

    def __init__(self):
        PollerInterface.__init__(self)
        self.dll = ctypes.cdll.LoadLibrary("/usr/lib/libevent.so")
        self.base = self.dll.event_base_new()

        self.pollables = set()
        self.arguments = {}

        self.evsignal = self.dll.event_new(self.base, signal.SIGINT,
          EV_SIGNAL|EV_PERSIST, _HANDLE_POLLER_EVENT, ctypes.py_object(self))
        self.event_add_(self.evsignal, None)

        self.sched(10, self.do_periodic_, self)

    def event_add_(self, event, timeo):
        self.dll.event_add(event, timeo)

    def event_del_(self, event):
        self.dll.event_del(event)

    def event_free_(self, event):
        self.dll.event_free(event)

    def event_new_(self, filenum, event, pyobject):
        return self.dll.event_new(self.base, filenum, event,
          _HANDLE_POLLABLE_EVENT, ctypes.py_object(pyobject))

    def register_pollable_(self, pollable):
        self.pollables.add(pollable)

    def unregister_pollable_(self, pollable):
        self.pollables.remove(pollable)

    def sched(self, delta, function, argument):
        pyobject = (function, argument, self)
        event = self.dll.event_new(self.base, -1, 0, _HANDLE_POLLER_EVENT,
                                   ctypes.py_object(pyobject))
        timeo = Timeval(int(math.floor(delta)), 0)
        self.dll.event_add(event, ctypes.pointer(timeo))
        self.arguments[pyobject] = event, timeo

    @staticmethod
    def do_periodic_(argument):
        # pylint: disable=W0702
        argument.sched(10, argument.do_periodic_, argument)
        for pollable in argument.pollables.copy():
            try:
                pollable.handle_periodic()
            except:
                logging.warning("unhandled exception", exc_info=1)

    def loop(self):
        self.dll.event_base_dispatch(self.base)

    def break_loop(self):
        self.dll.event_base_loopbreak(self.base)
