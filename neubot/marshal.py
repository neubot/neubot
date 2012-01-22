# neubot/marshal.py
# -*- coding: utf-8 -*-

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

import xml.dom.minidom
import urllib
import types
import sys
import cgi

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.compat import json

from neubot.utils import unicodize
from neubot.utils import stringify

# Marshal

def object_to_json(obj):
    return json.dumps(obj.__dict__)

def object_to_qs(obj):
    dictionary = {}
    for name, value in obj.__dict__.items():
        dictionary[name] = stringify(value)
    s = urllib.urlencode(dictionary)
    return s

def object_to_xml(obj):
    return dict_to_xml(obj.__class__.__name__, obj.__dict__)

def dict_to_xml(name, thedict):
    document = xml.dom.minidom.parseString("<" + name + "/>")

    root = document.documentElement
    root.appendChild( document.createTextNode("\r\n") )

    for name, value in thedict.items():

        if type(value) != types.ListType:
            value = [value]

        for v in value:
            root.appendChild( document.createTextNode("    ") )

            element = document.createElement(name)
            root.appendChild(element)
            element.appendChild( document.createTextNode( unicodize(v) ))

            root.appendChild( document.createTextNode("\r\n") )

    return root.toxml("utf-8")

MARSHALLERS = {
    "application/json": object_to_json,
    "application/x-www-form-urlencoded": object_to_qs,
    "application/xml": object_to_xml,
    "text/xml": object_to_xml,
}

def marshal_object(obj, mimetype):
    return MARSHALLERS[mimetype](obj)

# Unmarshal

def json_to_dictionary(s):
    return dict(json.loads(s))

def qs_to_dictionary(s):
    dictionary = {}
    for name, value in cgi.parse_qs(s).items():
        dictionary[name] = value[0]
    return dictionary

def xml_to_dictionary(s):
    dictionary = {}

    document = xml.dom.minidom.parseString(s)
    document.documentElement.normalize()        # XXX

    for element in document.documentElement.childNodes:
        if element.nodeType == element.ELEMENT_NODE:

            for node in element.childNodes:
                if node.nodeType == node.TEXT_NODE:

                    if not element.tagName in dictionary:
                        dictionary[element.tagName] = []

                    dictionary[element.tagName].append(node.data.strip())
                    break

    return dictionary

UNMARSHALLERS = {
    "application/json": json_to_dictionary,
    "application/x-www-form-urlencoded": qs_to_dictionary,
    "application/xml": xml_to_dictionary,
    "text/xml": xml_to_dictionary,
}

def unmarshal_objectx(s, mimetype, instance):
    dictionary = UNMARSHALLERS[mimetype](s)
    for name, value in instance.__dict__.items():
        if name in dictionary:
            nval = dictionary[name]
            if type(value) != types.ListType and type(nval) == types.ListType:
                nval = nval[0]
            setattr(instance, name, nval)

def unmarshal_object(s, mimetype, ctor):
    obj = ctor()
    unmarshal_objectx(s, mimetype, obj)
    return obj

# Unit test

import pprint

class Test(object):
    def __init__(self):
        # the city name that prompted all unicode issues...
        self.uname = u"Aglié"
        self.sname = "Aglie"
        self.fval = 1.43
        self.ival = 1<<17
        self.vect = [1,2,3,4,5,12,u"Aglié",1.43]
        self.v2 = ["urbinek"]

def test(mimetype):
    pprint.pprint("--- %s ---" % mimetype)
    m = Test()
    pprint.pprint(m.__dict__)
    e = marshal_object(m, mimetype)
    print e
    d = unmarshal_object(e, mimetype, Test)
    pprint.pprint(d.__dict__)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        mimetypes = MARSHALLERS.keys()
    else:
        mimetypes = sys.argv[1:]

    for mimetype in mimetypes:
        test(mimetype)
