# neubot/debug/__init__.py

#
# Copyright (c) 2010-2011 Simone Basso <bassosimone@gmail.com>,
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

import sys


class Profiler(object):

    def __init__(self):
        self.enabled = True
        self.frameno = 0
        self.depth = 0

    def _getfilename(self, frame):
        if frame.f_globals.has_key("__file__"):

            name = frame.f_globals["__file__"]
            if not name:
                # XXX this is quite unexpected
                name = "???"

            if name.endswith(".pyc") or name.endswith(".pyo"):
                name = name[:-1]
            for pattern in ["neubot/", "python2.5/", "python2.6/", "python/"]:
                index = name.find(pattern)
                if index > 0:
                    name = name[index+len(pattern):]
                    break

        else:
            name = "???"

        return name

    #
    # We stop tracing when we exit from the frame number zero.
    # This happens because we start tracing when the Python program
    # is already running, and so _our_ zero is actually a positive
    # frame number in Python's stack.
    # This is not a problem because usually we're interested in
    # tracing just a subset of the script.
    #
    # We also avoid diving into the logging module because this module
    # invokes loads of other functions of the standard python library,
    # and we are not actually interested on those functions.
    #

    def notify_event(self, frame, event, arg):
        if event in ["call", "return"]:

            fname = self._getfilename(frame)
            func = frame.f_code.co_name

            if event == "return":
                self.frameno -= 1
                if not self.enabled and self.frameno == self.depth:
                    self.enabled = True
                if self.frameno < 0:
                    sys.setprofile(None)
                    return

            if self.enabled:
                lineno = frame.f_lineno
                prefix  = "    " * self.frameno
                buff = "%s%s %s:%d:%s()\n" % (prefix,event,fname,lineno,func)
                sys.stderr.write(buff)

            if event == "call":
                if self.enabled and fname.startswith("logging/"):
                    self.enabled = False
                    self.depth = self.frameno
                self.frameno += 1


PROFILER = Profiler()
