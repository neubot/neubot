# neubot/debug.py
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
# Code for debugging
#

import sys

class Profiler:
    def __init__(self):
        self.enabled = True
        self.frameno = 0
        self.depth = 0

    def _getfilename(self, frame):
        if frame.f_globals.has_key("__file__"):
            name = frame.f_globals["__file__"]
            if name.endswith(".pyc") or name.endswith(".pyo"):
                name = name[:-1]
            for pattern in ["neubot/", "testing/", "python2.6/", "python/"]:
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
    # frame number in the Python stack.
    # This seems not a problem because usually we're interested
    # to trace just a subset of the script (for example the main()
    # function of neubot/main.py)
    #
    # We also avoid diving into the logging module because this module
    # invokes loads of other functions of the standard python library,
    # and we are not actually interested on those functions.  For the
    # same reason, we don't dive into the prettyprint_exception() func
    # of neubot.utils.
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
                if self.enabled and (fname.startswith("logging/") or (fname
                 == "neubot/utils.py" and func == "prettyprint_exception")):
                    self.enabled = False
                    self.depth = self.frameno
                self.frameno += 1

profiler = Profiler()
trace = profiler.notify_event

# To enable tracing, do
#sys.setprofile(neubot.debug.trace)