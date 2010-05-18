# neubot/application/_neubot.py
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
import sys
import time
import traceback

import neubot

from neubot.application.__defaults import defaults

def main(configuration, argv):
	sleeptime = 60
	logging.info("Merge configuration with defaults")
	for key, value in defaults.items():
		if (not configuration.has_key(key)):
			configuration[key] = value
	logging.info("Creating the poller")
	poller = neubot.network.poller()
	while (True):
		try:
			uri = configuration["server"]
			logging.info("Starting rendez-vous with '%s'" % uri)
			(scheme, address, port,
			    pathquery) = neubot.http.urlsplit(uri)
			neubot.simpleclient(poller, scheme, address, port)
			poller.loop()
		except Exception:
			logging.error("Rendez-vous with '%s' failed" % uri)
			lines = traceback.format_exc().splitlines()
			for line in lines:
				logging.info(line)
		logging.info("Now going to sleep for %d secs" % sleeptime)
		time.sleep(sleeptime)

if (__name__ == "__main__"):
	main(defaults, sys.argv)
