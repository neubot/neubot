#!/bin/sh -e

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
# Compile the mapping between the address of a node and the
# address of the corresponding sliver, making sure in the process
# that the node is up and running.
#

DEBUG=

SSH="$DEBUG $HOME/bin/mlab_ssh"

if [ $# -ne 0 ]; then
    echo 'Usage: $0' 1>&2
    exit 1
else

    # Start over
    rm -rf M-Lab/ip_addr.dat
    install -m644 /dev/null M-Lab/ip_addr.dat

    # Fetch the list of hosts in realtime
    HOSTS=$(./M-Lab/ls.py)

    COUNT=0
    for HOST in $HOSTS; do
        COUNT=$(($COUNT + 1))

        # Blank line before to separate each host logs
        echo ""
        echo "$HOST: start ip_addr"
        echo "$HOST: current host number $COUNT"

        #
        # Run the code below in the subshell, with set -e, so that
        # the first command that fails "throws an exception" and we
        # know something went wrong looking at $?.
        # We need to reenable errors otherwise the outer shell is
        # going to bail out if the inner one fails.
        #
        set +e
        (
            set -e

            # Make sure we can SSH into it
            echo "$HOST: make sure it's up and running"
            $SSH $HOST uname -a

            echo "$HOST neubot.mlab.$HOST" >> M-Lab/ip_addr.dat

        #
        # As soon as we exit from the subshell, save the errno and
        # re-enable errors, to catch potential doofus in the remainder
        # of the script.
        #
        )
        ERROR=$?
        set -e

        echo "$HOST: ip_addr result: $ERROR"
        echo "$HOST: ip_addr complete"

    done
fi
