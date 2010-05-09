# neubot/main.py
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

import ConfigParser
import getopt
import os
import pwd
import sys
import time

import neubot

USAGE = "Usage: neubot [-v] [-O key=value] [module [options]]\n"

conflist = [
	"/etc/neubot",
#	os.environ["HOME"] + "/" + ".neubot",		# FIXME
]

defaults = {
	"basedir": "/usr/share",
	"rendezvous": "http://whitespider.polito.it:9773/",
	"verbose": "False",
}

modules = {
}

def unixmain(args):
	commandline = {}
	try:
		opts, moduleargs = getopt.getopt(args, "O:v")
	except getopt.error:
		sys.stderr.write(USAGE)
		sys.exit(1)
	for opt, arg in opts:
		if (opt == "-v"):
			commandline["verbose"] = "True"
		elif (opt == "-O"):
			if (not "=" in arg):
				sys.stderr.write("Bad pair: %s\n", arg)
				sys.exit(1)
			key, value = arg.split("=", 1)
			if (not defaults.has_key(key)):
				sys.stderr.write("Unknow key: %s\n" % key)
				sys.exit(1)
			commandline[key] = value
	parser = ConfigParser.RawConfigParser()
	parser.add_section("neubot")
	for key, value in defaults.items():
		parser.set("neubot", key, value)
	for conffile in conflist:
		parser.read(conffile)
	for key, value in commandline.items():
		parser.set("neubot", key, value)
	if (len(moduleargs) > 0):
		mod = moduleargs[0]
		args = moduleargs[1:]
		if (not modules.has_key(mod)):
			sys.stderr.write("Unknown module: %s\n" % mod)
			sys.exit(1)
		modmain = modules[mod]
		modmain(parser.items(), args)
		sys.exit(0)
	if (os.getuid() == 0):
		entry = pwd.getpwnam("_neubot")
		os.setgid(entry.pw_gid)
		os.setuid(entry.pw_uid)
	neubot.openlog()
	neubot.daemonize()
	os.chdir("/")
	poller = neubot.network.poller()
	while (True):
		try:
			uri = parser.get("neubot", "rendezvous")
			neubot.http.client(poller, "HEAD", uri)
			poller.loop()
		except:
			pass
		time.sleep(300)
	sys.exit(0)
