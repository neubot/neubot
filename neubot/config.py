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

import StringIO
import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.marshal import unmarshal_objectx
from neubot.marshal import marshal_object

class Config(object):

    """
    Holds all the variables that it's possible to configure via
    the web user interface.  We return a JSON when the request
    is to read the current values.  And we expect an incoming and
    www-urlencoded string when the user wants to change some
    value.
    """

    def __init__(self):
        self.enabled = 1
        self.force = 0

    def dictionary(self):
        return vars(self)

    def marshal(self):
        data = marshal_object(self, "application/json")
        stringio = StringIO.StringIO(data)
        return stringio

    def update(self, stringio):
        data = stringio.read()
        unmarshal_objectx(data, "application/x-www-form-urlencoded", self)

CONFIG = Config()

__all__ = [ "CONFIG" ]

if __name__ == "__main__":
    stringio = CONFIG.marshal()
    print stringio.read()

    stringio = StringIO.StringIO()
    stringio.write("enabled=0&force=1")
    stringio.seek(0)

    CONFIG.update(stringio)

    stringio = CONFIG.marshal()
    print stringio.read()
