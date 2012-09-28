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
DEPLOY=1
FORCE=0

# Wrappers for ssh, scp
SCP="$DEBUG $HOME/bin/mlab_scp"
SSH="$DEBUG $HOME/bin/mlab_ssh"
SUDO="/usr/bin/sudo"

# Command line
args=$(getopt fn $*) || {
    echo "Usage: $0 [-nf] [host... ]" 1>&2
    echo "  -n : generate the tarball and exit" 1>&2
    echo "  -f : Force deployment when it is already deployed" 1>&2
    exit 1
}
set -- $args
while [ $# -gt 0 ]; do
    if [ "$1" = "-f" ]; then
        FORCE=1
        shift
    elif [ "$1" = "-n" ]; then
        DEPLOY=0
        shift
    elif [ "$1" = "--" ]; then
        shift
        break
    fi
done

destdir=dist/mlab
tarball=$destdir/neubot.tar.gz
version=$destdir/version

rm -rf -- $destdir
mkdir -p $destdir
$DEBUG git archive --format=tar --prefix=neubot/ HEAD|gzip -9 > $tarball
$DEBUG git describe --tags > $version

if [ "$DEPLOY" = "0" ]; then
    exit 0
fi

if [ $# -eq 0 ]; then
    # Fetch the list of hosts in realtime
    HOSTS=$(./M-Lab/ls.py)
else
    HOSTS=$*
fi

COUNT=0
for HOST in $HOSTS; do
    COUNT=$(($COUNT + 1))

    # Blank line before to separate each host logs
    echo ""
    echo "$HOST: start deploy"
    echo "$HOST: current host number $COUNT"

    #
    # Run the installation in the subshell with set -e so that
    # the first command that fails "throws an exception" and we
    # know something went wrong looking at $?.
    # We need to reenable errors otherwise the outer shell is
    # going to bail out if the inner one fails.
    #
    set +e
    (
        set -e

        DOINST=1
        if [ $FORCE -eq 0 ]; then
            echo "$HOST: do we need to resume?"
            if $SSH $HOST 'ps auxww|grep -q ^_neubot'; then
                DOINST=0
            fi
        fi

        if [ "$DOINST" = "1" ]; then
            echo "$HOST: stop and remove old neubot"
            stop_sh='/home/mlab_neubot/neubot/M-Lab/stop.sh'
            $SSH $HOST "if test -x $stop_sh; then $SUDO $stop_sh || true; fi"
            $SSH $HOST rm -rf neubot

            echo "$HOST: copy files"
            $SCP $tarball $HOST:
            $SCP $version $HOST:

            echo "$HOST: install new neubot"
            $SSH $HOST tar -xzf neubot.tar.gz
            $SSH $HOST python -m compileall -q neubot/neubot/

            echo "$HOST: start new neubot"
            $SSH $HOST $SUDO /home/mlab_neubot/neubot/M-Lab/install.sh
            $SSH $HOST $SUDO /etc/rc.d/rc.local

            echo "$HOST: cleanup"
            $SSH $HOST rm -rf neubot.tar.gz
        fi

        #
        # Make sure all our ports are bound on the virtualized
        # machine.  If they are not, Neubot may work but it hasn't
        # been deployed correctly and Thomas must be informed.
        # While there, make sure we've not been able to bind to
        # port 80, which should not happen.
        #
        echo "$HOST: make sure we've bind all ports"
        $SSH $HOST netstat -a --tcp -n | grep LISTEN \
               | awk '{print $4}' | sort > M-Lab/ports.new
        diff -u M-Lab/ports.txt M-Lab/ports.new

    #
    # As soon as we exit from the subshell, save the errno and
    # re-enable errors, to catch potential doofus in the remainder
    # of the script.
    #
    )
    ERROR=$?
    set -e

    echo "$HOST: deploy result: $ERROR"
    echo "$HOST: deploy complete"
done
