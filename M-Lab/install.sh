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
# Install Neubot on an M-Lab sliver.
# Remotely invoked on the sliver by M-Lab/deploy.sh.
#

DEBUG=
INSTALL="install -o 0 -g 0"

$DEBUG cd $(dirname $0)
$DEBUG $INSTALL rc.local /etc/rc.d/rc.local
$DEBUG $INSTALL rsyncd.conf /etc/rsyncd.conf
$DEBUG grep -q ^_neubot /etc/group || $DEBUG /usr/sbin/groupadd -r _neubot
$DEBUG grep -q ^_neubot /etc/passwd || \
       $DEBUG /usr/sbin/useradd -r -d/ -g_neubot -s/sbin/nologin _neubot
