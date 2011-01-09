# neubot/net/listeners.py

#
# Copyright (c) 2010 Simone Basso <bassosimone@gmail.com>,
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

#
# Non-blocking listen() and accept() for stream sockets
#

if __name__ == "__main__":
    from sys import path
    path.insert(0, ".")

from neubot.net.streams import create_stream
from neubot.net.pollers import Pollable, poller
from socket import SOCK_STREAM, AI_PASSIVE
from socket import error as SocketError
from neubot.utils import fixkwargs
from socket import getaddrinfo
from socket import SO_REUSEADDR
from socket import SOL_SOCKET
from socket import socket
from socket import AF_INET
from sys import exit
from neubot import log

from socket import AF_INET6
from neubot.net.streams import listen
from neubot.net.pollers import loop
from neubot import version
from getopt import GetoptError
from getopt import getopt
from sys import stdout
from sys import stderr
from sys import argv

USAGE = "Usage: %s [-6Vv] [-S certfile] [--help] address port\n"

HELP = USAGE +								\
"Options:\n"								\
"  -6          : Use IPv6 rather than IPv4.\n"				\
"  --help      : Print this help screen and exit.\n"			\
"  -S certfile : Use OpenSSL and the specified certfile.\n"		\
"  -V          : Print version number and exit.\n"			\
"  -v          : Run the program in verbose mode.\n"

def accepted(stream):
    stream.close()

def main(args):
    family = AF_INET
    secure = False
    certfile = None
    try:
        options, arguments = getopt(args[1:], "6S:Vv", ["help"])
    except GetoptError:
        stderr.write(USAGE % args[0])
        exit(1)
    for name, value in options:
        if name == "-6":
            family = AF_INET6
        elif name == "--help":
            stdout.write(HELP % args[0])
            exit(0)
        elif name == "-S":
            secure = True
            certfile = value
        elif name == "-V":
            stdout.write(version + "\n")
            exit(0)
        elif name == "-v":
            log.verbose()
    if len(arguments) != 2:
        stderr.write(USAGE % args[0])
        exit(1)
    listen(arguments[0], arguments[1], accepted, family=family,
     secure=secure, certfile=certfile)
    loop()

if __name__ == "__main__":
    main(argv)
