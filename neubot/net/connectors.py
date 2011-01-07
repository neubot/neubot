# neubot/net/connectors.py

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
# Non-blocking connect for stream sockets
#

if __name__ == "__main__":
    from sys import path
    path.insert(0, ".")

from neubot.net.streams import create_stream
from neubot.net.pollers import Pollable, poller
from neubot.utils import fixkwargs
from neubot.utils import ticks
from socket import error as SocketError
from socket import SOCK_STREAM
from errno import EINPROGRESS
from errno import EWOULDBLOCK
from socket import getaddrinfo
from errno import ENOTCONN
from socket import AF_INET6
from socket import AF_INET
from socket import socket
from neubot import log
from sys import exit
from os import strerror
from sys import argv

from neubot.net.pollers import loop
from neubot.net.streams import connect
from neubot import version
from getopt import GetoptError
from getopt import getopt
from sys import stdout
from sys import stderr

USAGE = "Usage: %s [-6SVv] [-n timeout] [--help] address port\n"

HELP = USAGE +								\
"Options:\n"								\
"  -6         : Use IPv6 rather than IPv4.\n"				\
"  --help     : Print this help screen and exit.\n"			\
"  -n timeout : Time-out after timeout seconds.\n"			\
"  -S         : Secure connect().  Use OpenSSL.\n"			\
"  -V         : Print version number and exit.\n"			\
"  -v         : Run the program in verbose mode.\n"

def connected(stream):
    stream.close()

def main(args):
    family = AF_INET
    timeout = 10
    secure = False
    try:
        options, arguments = getopt(args[1:], "6n:SVv", ["help"])
    except GetoptError:
        stderr.write(USAGE % args[0])
        exit(1)
    for name, value in options:
        if name == "-6":
            family = AF_INET6
        elif name == "--help":
            stdout.write(HELP % args[0])
            exit(0)
        elif name == "-n":
            try:
                timeout = int(value)
            except ValueError:
                timeout = -1
            if timeout < 0:
                log.error("Bad timeout")
                exit(1)
        elif name == "-S":
            secure = True
        elif name == "-V":
            stdout.write(version + "\n")
            exit(0)
        elif name == "-v":
            log.verbose()
    if len(arguments) != 2:
        stderr.write(USAGE % args[0])
        exit(1)
    connect(arguments[0], arguments[1], connected, conntimeo=timeout,
            family=family, secure=secure)
    loop()

if __name__ == "__main__":
    main(argv)
