# @DEST@

#
# Copyright (c) 2013
#     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
#     and Simone Basso <bassosimone@gmail.com>
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

""" The HTTPD server """

include(`m4/include/aaa_base.m4')

NEUBOT_PY3_READY()

import getopt
import logging
import os
import socket
import sys

NEUBOT_ADJUST_PYTHONPATH()

from neubot.http_proxy import HTTPConnectProxy
from neubot.http_proxy import HTTPProxyServer
from neubot.http_www import HTTPWWWServer
from neubot.http_www import HTTPSWWWServer
from neubot.network_select import SelectPoller

from neubot import utils_posix

USAGE = """\
usage: neubot httpd [-6CdJPv] [-A address] [-p port] [-r rootdir]
                    [-S certfile] [-u user]"""

def main(args):
    """ Main function """
    try:
        options, arguments = getopt.getopt(args[1:], "6A:CdJPp:r:S:u:v")
    except getopt.error:
        sys.exit(USAGE)
    if arguments:
        sys.exit(USAGE)

    family = socket.AF_INET
    address = "127.0.0.1"
    connect_proxy = False
    daemonize = 0
    jail = 0
    proxy_mode = False
    port = 8080
    rootdir = "."
    ssl_cert = None
    user = None
    level = logging.WARNING

    for name, value in options:
        if name == "-6":
            family = socket.AF_INET6
        elif name == "-A":
            address = value
        elif name == "-C":
            connect_proxy = True
        elif name == "-d":
            daemonize = 1
        elif name == "-J":
            jail = 1
        elif name == "-P":
            proxy_mode = True
        elif name == "-p":
            port = int(value)
        elif name == "-r":
            rootdir = value
        elif name == "-S":
            ssl_cert = value
        elif name == "-u":
            user = value
        elif name == "-v":
            level = logging.DEBUG

    logging.basicConfig(level=level, format="%(message)s")

    rootdir = os.path.abspath(rootdir)

    passwd = None
    if user:
        if os.getuid() == 0 or os.geteuid() == 0:
            logging.debug("Will drop privileges and become: %s", user)
            passwd = utils_posix.getpwnam(user)
        else:
            logging.warning("Running in user mode; cannot change user")

    poller = SelectPoller()

    if ssl_cert:
        logging.debug("Starting HTTPS web server...")
        server = HTTPSWWWServer(poller)
        server.rootdir = rootdir
        server.certfile = ssl_cert
    elif proxy_mode:
        logging.debug("Starting HTTP web proxy...")
        server = HTTPProxyServer(poller)
    elif connect_proxy:
        logging.debug("Starting HTTP CONNECT proxy...")
        server = HTTPConnectProxy(poller)
    else:
        logging.debug("Starting HTTP web server...")
        server = HTTPWWWServer(poller)
        server.rootdir = rootdir

    error = server.sock_bind(family, socket.SOCK_STREAM, address, port)
    if error:
        logging.error("FATAL: bind() failed")
        sys.exit(1)

    server.tcp_listen(128)
    server.tcp_wait_accept()

    # Must be before chroot, because it needs to open '/dev/null'
    if daemonize:
        utils_posix.daemonize()

    # Must be before chuser, because it needs root privileges
    if jail:
        logging.debug("About to enter into the chroot jail (CWD: %s)",
                      os.getcwd())
        os.chroot(rootdir)
        os.chdir("/")
        if hasattr(server, "rootdir"):
            server.rootdir = "/"
        logging.debug("We are now into the chroot jail (CWD: %s)",
                      os.getcwd())

    if passwd:
        utils_posix.chuser(passwd)

    if os.getuid() == 0 or os.geteuid() == 0:
        logging.error("FATAL: I refuse to run with root privileges")
        sys.exit(1)

    poller.loop()

if __name__ == "__main__":
    main(sys.argv)
