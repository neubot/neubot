# neubot/state.py

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
# Track neubot state
#

if __name__ == "__main__":
    from sys import path
    path.insert(0, ".")

from neubot.notify import STATECHANGE
from neubot.notify import get_event_timestamp
from neubot.utils import versioncmp
from neubot.utils import timestamp
from neubot.utils import XML_to_stringio
from xml.dom import minidom
from neubot.notify import publish
from neubot import version

class StateNegotiate:
    def __init__(self):
        self.queuePos = 0
        self.queueLen = 0

    #
    # ...
    #   <queuePos>7</queuePos>
    #   <queueLen>21</queueLen>
    # ...
    #

    def marshal(self, document, parent):
        element = document.createElement("queuePos")
        text = document.createTextNode(str(self.queuePos))
        element.appendChild(text)
        parent.appendChild(element)
        element = document.createElement("queueLen")
        text = document.createTextNode(str(self.queueLen))
        element.appendChild(text)
        parent.appendChild(element)

    def set_queueInfo(self, queuePos, queueLen):
        self.queuePos = queuePos
        self.queueLen = queueLen

# states
READY = "ready"
RUNNING = "running"
DONE = "done"

class StateTest:
    def __init__(self, name, tasks=[]):
        self.current = None
        self.name = name
        self.states = {}
        for task in tasks:
            self.states[task] = READY
        self.tasks = tasks
        self.results = []

    def complete(self):
        self.states[self.current] = DONE
        self.current = None

    def set_task(self, task):
        if self.current:
            self.states[self.current] = DONE
        self.states[task] = RUNNING
        self.current = task

    def append_result(self, tag, value, unit):
        self.results.append((tag, value, unit))

    #
    # ...
    #   <name>speedtest</name>
    #   <task state="done">latency</task>
    #   <task state="running">download</task>
    #   <task state="ready">upload</task>
    #   <result tag="latency" unit="s">0.0012</result>
    # ...
    #

    def marshal(self, document, parent):
        if self.name:
            element = document.createElement("name")
            text = document.createTextNode(self.name)
            element.appendChild(text)
            parent.appendChild(element)
        for task in self.tasks:
            statex = self.states[task]
            element = document.createElement("task")
            element.setAttribute("state", statex)
            text = document.createTextNode(task)
            element.appendChild(text)
            parent.appendChild(element)
        for tag, value, unit in self.results:
            element = document.createElement("result")
            element.setAttribute("tag", tag)
            element.setAttribute("unit", unit)
            text = document.createTextNode(str(value))
            element.appendChild(text)
            parent.appendChild(element)

class StateRendezvous:
    def __init__(self):
        self.status = None

    def set_status(self, status):
        self.status = status

    #
    # ...
    #   <status>failed</status>
    # ...
    #

    def marshal(self, document, parent):
        if self.status:
            element = document.createElement("status")
            text = document.createTextNode(self.status)
            element.appendChild(text)
            parent.appendChild(element)

#
# TODO It would be nice to use "idle" for activity instead of
# None because that will certainly make the code more readable
# for new developers.
#

ACTIVITIES = [
    "rendezvous",
    "negotiate",
    "test",
    "collect",
]

class State:

    #
    # We put versioninfo in the constructor because
    # it should always be visible and should never be
    # cleared when we change activity.
    #

    def __init__(self):
        self.versioninfo = ()
        self.rendezvous = None
        self.activity = None
        self.negotiate = None
        self.test = None
        self.since = timestamp()
        self.next_rendezvous = -1

    def set_next_rendezvous(self, t):
        self.next_rendezvous = t
        return self

    def set_versioninfo(self, ver, uri):
        self.versioninfo = (ver, uri)
        return self

    #
    # <state t="1284818634023">
    #  <since>1292599259</since>
    #  <next_rendezvous>1292599277</next_rendezvous>
    #  <active>True</active>
    #  <activity>rendezvous</activity>
    #  <activity>negotiate</activity>
    #  <activity current="true">test</activity>
    #  <activity>collect</activity>
    #  <negotiate>
    #    ...
    #  </negotiate>
    #  <test>
    #    ...
    #  </test>
    # </state>
    #

    def marshal(self):
        timestamp = get_event_timestamp(STATECHANGE)
        document = minidom.parseString("<state/>")
        root = document.documentElement
        root.setAttribute("t", timestamp)
        element = document.createElement("since")
        root.appendChild(element)
        text = document.createTextNode(str(self.since))
        element.appendChild(text)
        if self.next_rendezvous > 0:
            element = document.createElement("next_rendezvous")
            root.appendChild(element)
            text = document.createTextNode(str(self.next_rendezvous))
            element.appendChild(text)
        if len(self.versioninfo) == 2:
            ver, uri = self.versioninfo
            if versioncmp(ver, version) > 0:
                element = document.createElement("update")
                element.setAttribute("uri", uri)
                text = document.createTextNode(ver)
                element.appendChild(text)
                root.appendChild(element)
        element = document.createElement("active")
        if not self.activity:
            text = document.createTextNode("false")
        else:
            text = document.createTextNode("true")
        element.appendChild(text)
        root.appendChild(element)
        for activity in ACTIVITIES:
            element = document.createElement("activity")
            if activity == self.activity:
                element.setAttribute("current", "true")
            text = document.createTextNode(activity)
            element.appendChild(text)
            root.appendChild(element)
        if self.negotiate:
            element = document.createElement("negotiate")
            self.negotiate.marshal(document, element)
            root.appendChild(element)
        if self.test:
            element = document.createElement("test")
            self.test.marshal(document, element)
            root.appendChild(element)
        if self.rendezvous:
            element = document.createElement("rendezvous")
            self.rendezvous.marshal(document, element)
            root.appendChild(element)
        return XML_to_stringio(document)

    #
    # Return self because we want to combine
    # many function calls on the same line,
    # e.g. state.set_inactive("").commit()
    #

    def set_inactive(self):
        self.activity = None
        return self

    def set_activity(self, activity, tasks=[], name=""):
        if not activity in ACTIVITIES:
            raise ValueError("Invalid activity name: %s" % activity)
        #
        # When there is an Idle -> Busy transition we forget
        # the results of the previous test. We keep them while
        # we're idle so: (a) if an UI attaches while we are
        # idle it could show something; (b) there is not a race
        # condition between the browser and the Collect ->
        # Idle transition (that used to be the place where we
        # forgot the results).
        #
        if self.activity == None:
            self.rendezvous = None
            self.negotiate = None
            self.test = None
        self.activity = activity
        if activity == "negotiate":
            self.negotiate = StateNegotiate()
        elif activity == "test":
            self.test = StateTest(name, tasks)
        elif activity == "collect":
            self.test.complete()
        return self

    def set_task(self, task):
        if self.test:
            self.test.set_task(task)
        return self

    def set_queueInfo(self, queuePos, queueLen):
        if self.negotiate:
            self.negotiate.set_queueInfo(queuePos, queueLen)
        return self

    def set_rendezvous_status(self, status):
        if not self.rendezvous:
            self.rendezvous = StateRendezvous()
        self.rendezvous.set_status(status)
        return self

    def append_result(self, tag, value, unit):
        if self.test:
            self.test.append_result(tag, value, unit)
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

from sys import stdout

if __name__ == "__main__":
    PRINT = lambda: stdout.write(state.marshal().read() + "\n")
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
        state.append_result("latency", 0.013, "s")
        state.set_task("download").commit()
        PRINT()
        state.append_result("download", 11.1, "Mbit/s")
        state.set_task("upload").commit()
        PRINT()
        state.append_result("upload", 9.8, "Mbit/s")
        state.set_activity("collect").commit()
        PRINT()
        state.set_inactive()
        PRINT()
        count = count + 1
