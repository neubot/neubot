# neubot/application/_writeconfig.py
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
import logging
import sys

from neubot.application.__defaults import defaults

def main(configuration, argv):
	logging.info("Merging configuration with defaults")
	for key, value in defaults.items():
		if (not configuration.has_key(key)):
			configuration[key] = value
	configparser = ConfigParser.RawConfigParser(configuration)
	configparser.write(sys.stdout)
	sys.exit(0)

if (__name__ == "__main__"):
	main(defaults, sys.argv)
