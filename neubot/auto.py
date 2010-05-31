# neubot/auto.py
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

import getopt
import logging
import sys
import time

import neubot

USAGE =                                                                 \
"Usage:\n"                                                              \
"  neubot [options] auto [options] [uri]\n"                             \
"\n"                                                                    \
"Try `neubot measure --help' for more help.\n"

LONGOPTS = [
    "help",
    "sleep-time=",
]

HELP =                                                                  \
"Usage:\n"                                                              \
"  neubot [options] auto [options] [uri]\n"                             \
"\n"                                                                    \
"Options:\n"                                                            \
"  --help\n"                                                            \
"      Print this help screen.\n"                                       \
"  --sleep-time TIME\n"                                                 \
"      Time to sleep between each rendez-vous.\n"                       \
"\n"

def main(argv):
    sleeptime = 60
    rendezvousuri = "http://neubot.org:9773/rendez-vous/1.0"
    try:
        options, arguments = getopt.getopt(argv[1:], "", LONGOPTS)
    except getopt.error:
        sys.stderr.write(USAGE)    # FIXME
        sys.exit(1)
    for name, value in options:
        if name == "--help":
            sys.stdout.write(HELP)
            sys.exit(0)
        elif name == "--sleep-time":
            try:
                sleeptime = int(value)
            except ValueError:
                sleeptime = -1
            if sleeptime < 0:
                logging.error("Bad argument to --sleep-time")
                sys.exit(1)
    if len(arguments) >= 2:
        sys.stderr.write(USAGE)
        sys.exit(1)
    elif len(arguments) == 1:
        rendezvousuri = arguments[0]
    logging.info("Running in automatic mode")
    poller = neubot.network.poller()
    while True:
        logging.info("Going to sleep for %s seconds" % sleeptime)
        time.sleep(sleeptime)
        try:
            client = neubot.nrendezvous.client(poller, uri=rendezvousuri)
            client.accept_test("http")
            client.set_version(neubot.version)
            poller.loop()
            todolist = client.responsebody
            if (todolist.versioninfo.has_key(u"version") and
              todolist.versioninfo.has_key(u"uri")):
                version = todolist.versioninfo[u"version"]
                updateuri = todolist.versioninfo[u"uri"]
                if neubot.utils.versioncmp(version, neubot.version) > 0:
                    logging.warning("New version %s available at %s" % (
                                    version, updateuri))
            try:
                negotiateuri = todolist.available["http"]
                #
                # FIXME More in detail we need to wrap the message so
                # that we do not need to be aware of the underlying
                # technology (e.g. JSON, XML.) -- in addition we should
                # provide the required accessors to avoid, e.g. the
                # below problem that we must convert manually.
                #
                negotiateuri = str(negotiateuri)
            except Exception:
                logging.warning("There are no available test I can perform")
                continue
            client = neubot.negotiate.client(poller, negotiateuri)
            client.set_direction("download")
            client.set_length((1<<16))
            poller.loop()
            params = client.params
            uri = params.uri
            uri = str(uri)    # FIXME See above
            client = neubot.measure.client(poller, uri, connections=1)
            poller.loop()
        except Exception:
            neubot.utils.prettyprint_exception()

if (__name__ == "__main__"):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    main(sys.argv)
