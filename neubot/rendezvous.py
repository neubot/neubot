# neubot/rendezvous.py
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

import json
import types

def prettyprinter(write, prefix, message, eol=""):
	obj = json.loads(str(message))
	lines = json.dumps(obj, ensure_ascii=True, indent=1)
	for line in lines.splitlines():
		write(prefix + line + eol)

class clientinfo:
	def __init__(self, octets=""):
		self.accepts = []
		self.provides = {}
		self.version = u""
		if (octets):
			dictionary = json.loads(octets)
			if (type(dictionary) != types.DictType):
				raise (ValueError("Bad json message"))
			if (dictionary.has_key(u"accepts")):
				for accept in dictionary[u"accepts"]:
					if (type(accept) != types.UnicodeType):
						raise (ValueError(
						    "Bad json message"))
					self.accepts.append(accept)
			if (dictionary.has_key(u"provides")):
				provides = dictionary[u"provides"]
				if (type(provides) != types.DictType):
					raise (ValueError("Bad json message"))
				for name, uri in provides.items():
					if (type(name) != types.UnicodeType):
						raise (ValueError(
						    "Bad json message"))
					if (type(uri) != types.UnicodeType):
						raise (ValueError(
						    "Bad json message"))
					self.provides[name] = uri
			if (dictionary.has_key(u"version")):
				version = dictionary[u"version"]
				if (type(version) != types.UnicodeType):
					raise (ValueError("Bad json message"))
				self.version = version

	def __str__(self):
		dictionary = {}
		if (len(self.accepts) > 0):
			dictionary[u"accepts"] = self.accepts
		if (len(self.provides) > 0):
			dictionary[u"provides"] = self.provides
		if (len(self.version) > 0):
			dictionary[u"version"] = self.version
		octets = json.dumps(dictionary, ensure_ascii=True)
		return (octets)

	def accept_test(self, name):
		self.accepts.append(unicode(name))

	def provide_test(self, name, uri):
		self.provides[unicode(name)] = unicode(uri)

	def set_version(self, version):
		self.version = unicode(version)

class todolist:
	def __init__(self, octets=""):
		self.versioninfo = {}
		self.available = {}
		if (octets):
			dictionary = json.loads(octets)
			if (type(dictionary) != types.DictType):
				raise (ValueError("Bad json message"))
			if (dictionary.has_key(u"versioninfo")):
				versioninfo = dictionary[u"versioninfo"]
				if (type(versioninfo) != types.DictType):
					raise (ValueError("Bad json message"))
				for key, value in versioninfo.items():
					if (type(key) != types.UnicodeType):
						raise (ValueError(
						    "Bad json message"))
					if (type(value) != types.UnicodeType):
						raise (ValueError(
						    "Bad json message"))
					self.versioninfo[key] = value
			if (dictionary.has_key(u"available")):
				available = dictionary[u"available"]
				if (type(available) != types.DictType):
					raise (ValueError("Bad json message"))
				for name, uri in available.items():
					if (type(name) != types.UnicodeType):
						raise (ValueError(
						    "Bad json message"))
					if (type(uri) != types.UnicodeType):
						raise (ValueError(
						    "Bad json message"))
					self.available[name] = uri

	def __str__(self):
		dictionary = {}
		if (len(self.versioninfo) > 0):
			dictionary[u"versioninfo"] = self.versioninfo
		if (len(self.available) > 0):
			dictionary[u"available"] = self.available
		octets = json.dumps(dictionary, ensure_ascii=True)
		return (octets)

	def set_versioninfo(self, version, uri):
		self.versioninfo[u"version"] = unicode(version)
		self.versioninfo[u"uri"] = unicode(uri)

	def add_available(self, name, uri):
		self.available[unicode(name)] = unicode(uri)
