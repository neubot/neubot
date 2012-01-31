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
# Script to start Neubot on M-Lab slivers
#

DEBUG=
$DEBUG /etc/init.d/rsyslog restart
#
# Must redirect stdin to /dev/null because if the input is a socket
# rsync believes it has been invoked by inetd and tries to negotiate
# with us.
#
$DEBUG rsync --daemon < /dev/null
$DEBUG /usr/bin/python /home/mlab_neubot/neubot/neubot/main/__init__.py server
