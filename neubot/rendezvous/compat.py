# neubot/rendezvous/compat.py

#
# Copyright (c) 2011 Simone Basso <bassosimone@gmail.com>,
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
# For now, this file contains the message-handling code that
# used to live in __init__.py but I would like it to evolve and
# eventually hide JSON/XML differencies.
#

import xml.dom.minidom

class RendezvousRequest(object):
    def __init__(self):
        self.accept = []
        self.version = ""
        self.privacy_informed = 0
        self.privacy_can_collect = 0
        self.privacy_can_share = 0

class RendezvousResponse(object):
    def __init__(self):
        self.update = {}
        self.available = {}

#
# Backward-compat ad-hoc stuff.  BLEAH.
#
# <rendezvous_response>
#  <available name="speedtest">
#   <uri>http://speedtest1.neubot.org/speedtest</uri>
#   <uri>http://speedtest2.neubot.org/speedtest</uri>
#  </available>
#  <update uri="http://releases.neubot.org/neubot-0.2.4.exe">0.2.4</update>
# </rendezvous_response>
#

def adhoc_element(document, root, name, value, attributes):
    element = document.createElement(name)
    root.appendChild(element)

    if value:
        text = document.createTextNode(value)
        element.appendChild(text)

    if attributes:
        for name, value in attributes.items():
            element.setAttribute(name, value)

    return element

def adhoc_marshaller(obj):
    document = xml.dom.minidom.parseString("<rendezvous_response/>")

    if obj.update:
        adhoc_element(document, document.documentElement, "update",
          obj.update["version"], {"uri": obj.update["uri"]})

    for name, vector in obj.available.items():
        element = adhoc_element(document, document.documentElement,
          "available", None, {"name": name})

        for uri in vector:
            adhoc_element(document, element, "uri", uri, None)

    return document.documentElement.toxml("utf-8")
