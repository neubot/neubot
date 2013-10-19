#!/bin/sh

#
# Copyright (c) 2011 Simone Basso <bassosimone@gmail.com>,
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
# Smoke test for the negotiator
#

if [ "$1" = "--server" ]; then
    ./UNIX/bin/neubot server -D server.daemonize=0 -D server.debug=1
elif [ "$1" = "--speedtest" ]; then
    ./UNIX/bin/neubot speedtest -Dspeedtest.client.uri=http://127.0.0.1:9773/ \
                              -D runner.enabled=0
elif [ "$1" = "--bittorrent" ]; then
    ./UNIX/bin/neubot bittorrent -D bittorrent.address=127.0.0.1 \
                        -D bittorrent.negotiate.port=9773 \
                              -D runner.enabled=0
elif [ "$1" = "--speedtest-client" ]; then
    while ! test -f STOP; do
        $0 --speedtest
    done
elif [ "$1" = "--bittorrent-client" ]; then
    while ! test -f STOP; do
        $0 --bittorrent
    done
elif [ "$1" = "-9" ]; then
    for I in 1 2 3 4 5 6 7 8 9; do
        $0 --speedtest-client &
        $0 --bittorrent-client &
    done
elif [ "$1" = "--kill" ]; then
    ps auxww|grep smoke.sh|grep -v grep|awk '{print $2}'|xargs kill -9
else
    #
    # Optimize for the case when we're run from `make regress`
    # automatically and provide an insightful message.
    #
    echo "This test cannot run automatically"
    echo "Usage: $0 [-9|--kill|--server]"
    exit 0
fi
