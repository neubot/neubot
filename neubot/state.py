# neubot/state.py
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
# Track neubot state
#

if __name__ == "__main__":
    from sys import path
    path.insert(0, ".")

from neubot.notify import STATECHANGE
from neubot.notify import get_event_timestamp
from xml.etree.ElementTree import ElementTree
from xml.etree.ElementTree import TreeBuilder
from neubot.utils import versioncmp
from neubot.notify import publish
from neubot import version
from StringIO import StringIO

ACTIVITIES = [
    "rendezvous",
    "negotiate",
    "test",
    "collect",
]

# states
READY = "ready"
RUNNING = "running"
DONE = "done"

class State:

    #
    # We put versioninfo in the constructor because
    # it should always be visible and should never be
    # cleared when we change activity.
    #

    def __init__(self):
        self.versioninfo = ()
        self.set_inactive()

    def set_versioninfo(self, ver, uri):
        self.versioninfo = (ver, uri)

    #
    # <state t="1284818634023">
    #  <active>True</active>
    #  <activity>rendez-vous</activity>
    #  <activity>negotiate</activity>
    #  <activity current="true">testing</activity>
    #  <activity>collect</activity>
    #  <current>
    #   <name>speedtest</name>
    #   <task state="done">latency</task>
    #   <task state="running">speedtest</task>
    #   <task state="ready">upload</task>
    #  </current>
    # </state>
    #

    def marshal(self):
        builder = TreeBuilder()
        builder.start("state", {"t": get_event_timestamp(STATECHANGE)})
        self.marshal_versioninfo(builder)
        self.marshal_inactive(builder)
        for activity in ACTIVITIES:
            self.marshal_activity(builder, activity)
        builder.end("state")
        return self.make_xml(builder.close())

    def marshal_versioninfo(self, builder):
        if len(self.versioninfo) == 2:
            ver, uri = self.versioninfo
            if versioncmp(ver, version) > 0:
                builder.start("update", {"uri": uri})
                builder.data(ver)
                builder.end("update")

    def marshal_inactive(self, builder):
        builder.start("active", {})
        if self.inactive:
            builder.data("false")
        else:
            builder.data("true")
        builder.end("active")

    def marshal_activity(self, builder, activity):
        dictionary = {}
        current = (activity == self.current)
        if current:
            dictionary = {"current": "true"}
        builder.start("activity", dictionary)
        builder.data(activity)
        builder.end("activity")
        if current:
            builder.start("current", {})
            # XXX hook/hack
            if self.current == "test":
                if self.currentname:
                    builder.start("name", {})
                    builder.data(self.currentname)
                    builder.end("name")
                for task in self.tasknames:
                    builder.start("task", {"state": self.tasks[task]})
                    builder.data(task)
                    builder.end("task")
                if self.results:
                    for tag, value, unit in self.results:
                        builder.start("result", {"tag": tag, "unit": unit})
                        builder.data(str(value))
                        builder.end("result")
            elif self.current == "negotiate":
                if self.queuePos > 0:
                    builder.start("queuePos", {})
                    builder.data(str(self.queuePos))
                    builder.end("queuePos")
                if self.queueLen > 0:
                    builder.start("queueLen", {})
                    builder.data(str(self.queueLen))
                    builder.end("queueLen")
            builder.end("current")

    def make_xml(self, root):
        tree = ElementTree(root)
        stringio = StringIO()
        # damn! the output is not pretty
        tree.write(stringio, encoding="utf-8")
        stringio.seek(0)
        return stringio

    #
    # Return self because we want to combine
    # many function calls on the same line,
    # e.g. state.set_inactive("").commit()
    #

    def set_inactive(self):
        self.inactive = True
        self.currentname = ""
        self.current = ""
        self.tasknames = []
        self.tasks = {}
        self.running = ""
        self.results = []
        self.queuePos = 0
        self.queueLen = 0
        return self

    def set_activity(self, activity, tasks=[], name=""):
        if not activity in ACTIVITIES:
            raise ValueError("Invalid activity name: %s" % activity)
        self.set_inactive()
        self.inactive = False
        self.current = activity
        self.tasknames = tasks
        self.currentname = name
        for task in tasks:
            self.tasks[task] = READY
        return self

    def set_task(self, task):
        if self.running:
            self.tasks[self.running] = DONE
        self.tasks[task] = RUNNING
        self.running = task
        return self

    def set_queueInfo(self, queuePos, queueLen):
        self.queuePos = queuePos
        self.queueLen = queueLen
        return self

    def append_result(self, tag, value, unit):
        self.results.append((tag, value, unit))
        return self

    def commit(self):
        publish(STATECHANGE)
        return self

#
# We expect to be used as follows::
#  from neubot import state
#  ...
#  state.set_inactive().commit()
#

state = State()

#
# Unit testing
#

from xml.dom import minidom
from sys import stdout

def _XML_prettyprint(bytes):
    stdout.write(minidom.parseString(bytes).toprettyxml(
     indent="  ", newl="\n", encoding="utf-8") + "\n")

if __name__ == "__main__":
    PRINT = lambda: _XML_prettyprint(state.marshal().read())
    TASKS = ["latency", "download", "upload"]
    count = 0
    state.set_versioninfo("0.7.3", "http://packages.neubot.org/latest")
    PRINT()
    while count < 2:
        state.set_activity("negotiate").set_queueInfo("2", "3").commit()
        PRINT()
        state.set_queueInfo("1", "3").commit()
        PRINT()
        state.set_activity("test", TASKS).set_task("latency").commit()
        PRINT()
        state.append_result("latency", 0.012, "s")
        state.append_result("latency", 0.013, "s")
        state.set_task("download").commit()
        PRINT()
        state.append_result("download", 11.1, "MB/s")
        state.set_task("upload").commit()
        PRINT()
        state.set_inactive()
        PRINT()
        count = count + 1
