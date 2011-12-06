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

DEBUG=

# Prerequisites
HOSTS=$HOME/etc/mlab/hosts
SCP=$HOME/bin/mlab_scp
SSH=$HOME/bin/mlab_ssh

$DEBUG git archive --format=tar --prefix=neubot/ -o M-Lab/neubot.tar HEAD
$DEBUG gzip -9 M-Lab/neubot.tar
$DEBUG git log --oneline|head -n1 > M-Lab/version

for HOST in $(cat $HOSTS); do

    # Blank line before to separate each host logs
    echo ""
    echo "$HOST: start deploy"

    echo "$HOST: make sure it's up and running"
    $DEBUG ping -c3 $HOST 1>/dev/null 2>/dev/null || continue

    echo "$HOST: stop and remove old neubot"
    $DEBUG $SSH $HOST 'sudo /home/mlab_neubot/neubot/M-Lab/stop.sh || true'
    $DEBUG $SSH $HOST rm -rf neubot

    echo "$HOST: copy files"
    $DEBUG $SCP M-Lab/neubot.tar.gz $HOST:
    $DEBUG $SCP M-Lab/version $HOST:

    echo "$HOST: install new neubot"
    $DEBUG $SSH $HOST tar -xzf neubot.tar.gz
    $DEBUG $SSH $HOST python -m compileall neubot/neubot/

    echo "$HOST: start new neubot"
    $DEBUG $SSH $HOST sudo /home/mlab_neubot/neubot/M-Lab/install.sh
    $DEBUG $SSH $HOST sudo /etc/rc.local

    echo "$HOST: cleanup"
    $DEBUG $SSH $HOST rm -rf neubot.tar.gz

    echo "$HOST: deploy complete"

done
