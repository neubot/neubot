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
# Script to start Neubot on the master server
# Adapted from M-Lab/start.sh
#

DEBUG=
INSTDIR=/home/simone/neubot
PYTHON=/usr/bin/python

[ $(id -u) -eq 0 ] || { echo 'you must be root' 1>&2; exit 1; }

$DEBUG $INSTDIR/MasterSrv/stop.sh
$DEBUG /bin/sh $INSTDIR/MasterSrv/redir_table.sh

$DEBUG sqlite3 /var/lib/neubot/database.sqlite3 'select * from geoloc';
$DEBUG echo 'If the GEOLOC table looks ugly, hit ^C NOW!'
$DEBUG sleep 3

[ -f $INSTDIR/../neubot_cmdline ] && . $INSTDIR/../neubot_cmdline

$DEBUG $PYTHON $INSTDIR/neubot/main/__init__.py server			\
	-D server.rendezvous=1 $NEUBOT_CMDLINE_EXTRA
