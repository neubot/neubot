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
# Script to check Neubot deployment on M-Lab slivers - Invoked on
# the sliver by init/initialize.sh.
#
# Note: port 7999 (rsync) is now managed by M-Lab scripts; therefore,
# we don't need to worry about it anymore.
#

. /etc/mlab/slice-functions

PORTS="ports_ipv6.txt"
if [ -z "`get_slice_ipv6`" ]; then
    PORTS="ports_ipv4.txt"
fi

echo "make sure we've bind all ports"
netstat -a --tcp -n | grep LISTEN | grep -v 7999 | awk '{print $4}' \
    | sort > neubot/M-Lab/ports.new
diff -u neubot/M-Lab/$PORTS neubot/M-Lab/ports.new
