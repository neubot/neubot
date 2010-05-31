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

import logging
import sys

import neubot

maintbl = {
    "auto"        : neubot.auto.main,
    "rendezvous"  : neubot.nrendezvous.main,
    "measure"     : neubot.measure.main,
    "negotiate"   : neubot.negotiate.main,
}

def main(argv):
    command = argv[0]
    try:
        mainfunc = maintbl[command]
    except KeyError:
        logging.error("The '%s' command does not exist." % command)
        logging.error("Here's a list of available commands:")
        for key in maintbl.keys():
            logging.error("  %s" % key)
        sys.exit(1)
    try:
        mainfunc(argv)
    except SystemExit:
        neubot.utils.prettyprint_exception(logging.info)
    except:
        neubot.utils.prettyprint_exception()
        sys.exit(1)
