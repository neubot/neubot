#!/bin/sh -e

#
# Copyright (c) 2011, 2013
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

#
# Script to stop Neubot on M-Lab slivers - Invoked on the sliver
# by init/stop.sh.
#

DEBUG=

if [ `id -u` -ne 0 ]; then
    echo "$0: FATAL: need root privileges" 1>&2
    exit 1
fi

# Note: the daemon should remove the pidfile before exiting
if [ -f /var/run/neubot.pid ]; then
    echo "kill old neubot process"
    $DEBUG kill -TERM $($DEBUG cat /var/run/neubot.pid) || true
fi
