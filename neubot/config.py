# neubot/config.py

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
# Most of the variables you can configure via UI
#

from StringIO import StringIO
from xml.etree.ElementTree import ElementTree
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement
from cgi import parse_qs

class Config:
    def __init__(self):
        self.enabled = True
        self.force = False

    def marshal(self):
        root = Element("config")
        elem = SubElement(root, "enabled")
        elem.text = str(self.enabled)
        elem = SubElement(root, "force")
        elem.text = str(self.force)
        tree = ElementTree(root)
        stringio = StringIO()
        tree.write(stringio, encoding="utf-8")
        stringio.seek(0)
        return stringio

    def _to_boolean(self, value):
        value = value.lower()
        if value in ["false", "no", "0"]:
            return False
        return True

    def update(self, stringio):
        body = stringio.read()
        dictionary = parse_qs(body)
        if dictionary.has_key("enabled"):
            value = dictionary["enabled"][0]
            self.enabled = self._to_boolean(value)
        if dictionary.has_key("force"):
            value = dictionary["force"][0]
            self.force = self._to_boolean(value)

config = Config()

if __name__ == "__main__":
    stringio = StringIO()
    stringio.write("enabled=False&force=True")
    stringio.seek(0)
    config.update(stringio)
    stringio = config.marshal()
    print stringio.read()
