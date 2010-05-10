# neubot/testing/http.py
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
# DEPRECATED -- use neubot/testing/getter.py instead
#

import getopt
import logging
import socket
import sys

import neubot

USAGE = "Usage: python %s [-46v] uri [uri ...]\n"

def main():
	family = socket.AF_UNSPEC
	verbose = False
	try:
		opts, uris = getopt.getopt(sys.argv[1:], "46v")
	except getopt.error:
		sys.stderr.write(USAGE % sys.argv[0])
		sys.exit(1)
	for opt, arg in opts:
		if (opt == "-4"):
			family = socket.AF_INET
		elif (opt == "-6"):
			family = socket.AF_INET6
		elif (opt == "-v"):
			verbose = True
	if (len(uris) == 0):
		sys.stderr.write(USAGE % sys.argv[0])
		sys.exit(1)
	if (verbose):
		logger = logging.getLogger()
		logger.setLevel(logging.DEBUG)
	poller = neubot.network.poller()
	for uri in uris:
		neubot.http.client(poller, "GET", uri, prettyprint=verbose)
	poller.loop()
	sys.exit(0)

if (__name__ == "__main__"):
	main()
