# neubot/utils.py
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

import logging
import logging.handlers
import os
import sys
import traceback

def prettyprint_exception(write=logging.error, eol=""):
	content = traceback.format_exc()
	for ln in content.splitlines():
		write(ln + eol)

def daemonize():
	if (os.name == "posix"):
		pid = os.fork()
		if (pid):
			sys.exit(0)
		os.setsid()
		pid = os.fork()
		if (pid):
			sys.exit(0)
		for fdesc in range(0,3):
			os.close(fdesc)
		for mode in ["r", "w", "w"]:
			open("/dev/null", mode)
	else:
		sys.stderr.write("daemonize(): not implemented\n")

def getprogname():
	vec = sys.argv[0].split("/")
	progname = vec[len(vec) - 1]
	return (progname)

def openlog():
	if (os.name == "posix"):
		progname = getprogname()
		root = logging.getLogger()
		handler = logging.handlers.SysLogHandler("/dev/log")
		formatter = logging.Formatter(progname + ": %(message)s")
		handler.setFormatter(formatter)
		root.addHandler(handler)				# XXX
	else:
		sys.stderr.write("openlog(): not implemented\n")
