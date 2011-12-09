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
# This script is used to compile the mapping between the
# FQDN of an M-Lab site and the *actual* address of the
# sliver inside the site.
#

DEBUG=

SSH="$DEBUG $HOME/bin/mlab_ssh"

if [ $# -gt 1 ]; then
    echo 'Usage: $0 [hostname]' 1>&2
    exit 1
elif [ $# -eq 1 ]; then
    $SSH $1 "/sbin/ifconfig|perl -ne 'print \$1 if (/inet addr:(.*) Bcast/)'"
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
        echo "$HOST: start geoloc"
        echo "$HOST: current host number $COUNT"

        echo "$HOST: make sure it's up and running"
        $DEBUG ping -c3 $HOST 1>/dev/null 2>/dev/null || continue

        echo "$HOST: get *real* IP address"
        ADDRESS=$($0 $HOST) || continue
        echo "$HOST $ADDRESS" >> M-Lab/ip_addr.dat

        echo "$HOST: geoloc complete"
    done

fi
