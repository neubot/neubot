# neubot/coordinate.py
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
import os
import sys

import neubot

def main(argv):
    arguments = argv[1:]
    if len(arguments) != 2:
        sys.stderr.write("Usage: neubot coordinate file address\n")
        sys.exit(1)
    filename = arguments[0]
    address = arguments[1]
    f = open(filename, "rb")
    f.seek(0, os.SEEK_END)
    length = f.tell()
    f.close()
    test_uri = "http://" + address + ":9090/"
    collect_uri = "http://" + address + ":9773/collect/1.0/"
    negotiate_uri = "http://" + address + ":9773/http/1.0/"
    poller = neubot.network.poller()
    container = neubot.container.container(poller, address="0.0.0.0",
                                           port="9773")
    servlet = neubot.negotiate.servlet(length, test_uri)
    container.register("/http/1.0/", servlet.main)
    servlet = neubot.rendezvous.servlet()
    servlet.set_versioninfo(neubot.version, "http://www.neubot.org:8080/")
    servlet.set_collecturi(collect_uri)
    servlet.add_available("http", negotiate_uri)
    container.register("/rendez-vous/1.0/", servlet.main)
    neubot.measure.server(poller, address="0.0.0.0", port="9090",
                          myfile=filename)
    servlet = neubot.collect.servlet()
    container.register("/collect/1.0/", servlet.main)
    poller.loop()

if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    main(sys.argv)
