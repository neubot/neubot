#!/bin/sh -e

#
# Copyright (c) 2011-2012 Simone Basso <bassosimone@gmail.com>,
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
# Deploy Neubot to M-Lab slivers
#

DEBUG=
RESUME=0

# Wrappers for ssh, scp
SCP="$DEBUG $HOME/bin/mlab_scp"
SSH="$DEBUG $HOME/bin/mlab_ssh"

# Command line
while [ $# -gt 0 ]; do
    if [ "$1" = "-r" ]; then
        RESUME=1
    else
        echo "Usage: $0 [-r]" 1>&2
        exit 1
    fi
    shift
done

if [ -f M-Lab/neubot.tar.gz ]; then
    echo "error: Working directory not clean" 1>&2
    exit 1
fi

$DEBUG git archive --format=tar --prefix=neubot/ -o M-Lab/neubot.tar HEAD
$DEBUG gzip -9 M-Lab/neubot.tar
$DEBUG git log --oneline|head -n1 > M-Lab/version

# Fetch the list of hosts in realtime
HOSTS=$(./M-Lab/ls.py)

COUNT=0
for HOST in $HOSTS; do
    COUNT=$(($COUNT + 1))

    # Blank line before to separate each host logs
    echo ""
    echo "$HOST: start deploy"
    echo "$HOST: current host number $COUNT"

    echo "$HOST: make sure it's up and running"
    $DEBUG ping -c3 $HOST 1>/dev/null 2>/dev/null || continue

    if [ $RESUME -ne 0 ]; then
        echo "$HOST: check whether we need to resume"
        {
            $SSH $HOST 'ps auxww|grep ^_neubot' && {
                echo "$HOST: deploy complete"
                continue
            } || true
        }
    fi

    echo "$HOST: stop and remove old neubot"
    $SSH $HOST 'sudo /home/mlab_neubot/neubot/M-Lab/stop.sh || true' || continue
    $SSH $HOST rm -rf neubot || continue

    echo "$HOST: copy files"
    $SCP M-Lab/neubot.tar.gz $HOST: || continue
    $SCP M-Lab/version $HOST: || continue

    echo "$HOST: install new neubot"
    $SSH $HOST tar -xzf neubot.tar.gz || continue
    $SSH $HOST python -m compileall neubot/neubot/ || continue

    echo "$HOST: start new neubot"
    $SSH $HOST sudo /home/mlab_neubot/neubot/M-Lab/install.sh || continue
    $SSH $HOST sudo /etc/rc.d/rc.local || continue

    echo "$HOST: cleanup"
    $SSH $HOST rm -rf neubot.tar.gz || continue

    echo "$HOST: deploy complete"

done
