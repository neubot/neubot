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
# Install Neubot on an a master server.
# Remotely invoked on the server by MasterSrv/deploy.sh.
# Adapted from M-Lab/install.sh
#

APTGET=/usr/bin/apt-get
DEBUG=
GUNZIP=/bin/gunzip
INSTALL="/usr/bin/install -o 0 -g 0"
RM=/bin/rm
SUDO=/usr/bin/sudo
URIBASE=http://geolite.maxmind.com
URIPATH=/download/geoip/database/GeoLiteCountry/GeoIP.dat.gz
WGET=/usr/bin/wget

$DEBUG cd $(dirname $0)
$DEBUG $APTGET install sqlite3 python-geoip wget
$DEBUG $INSTALL rc.local /etc/rc.local
$DEBUG /bin/grep -q ^_neubot /etc/group || $DEBUG /usr/sbin/groupadd -r _neubot
$DEBUG /bin/grep -q ^_neubot /etc/passwd || \
       $DEBUG /usr/sbin/useradd -r -d/ -g_neubot -s/sbin/nologin _neubot
$DEBUG $INSTALL -d /var/lib/neubot

$DEBUG $INSTALL -d /usr/local/share/GeoIP
$DEBUG $SUDO -u _neubot $WGET -O- $URIBASE$URIPATH|$GUNZIP > GeoIP.dat
$DEBUG $INSTALL -m400 GeoIP.dat /usr/local/share/GeoIP
$DEBUG $RM GeoIP.dat
