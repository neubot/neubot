#!/bin/sh

#
# Copyright (c) 2011 Alessio Palmero Aprosio <alessio@apnetwork.it>
#  Universita` degli Studi di Milano
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
# start.sh -- Really start this version of neubot under MacOSX
#

set -e

#
# The caller will use an absolute PATH so we can easily get
# the place where Neubot is installed using dirname.
#
VERSIONDIR=$(dirname $0)

logger -p daemon.info -t $0 "Neubot versiondir: $VERSIONDIR"

#
# Invoke the prerun.sh script which will make sure that Neubot
# will run (for example it will check that the required users and
# groups exist and so on and so forth).
# We invoke it unconditionally and it's up to the script to see
# whether it needs to do something or not.
#
$VERSIONDIR/prerun.sh

#
# Start the current version of Neubot.  Note that we don't
# go in the background because launchd(8) will be confused by
# that.
# We don't invoke updater/unix.py via main/__init__.py
# because unix.py is python3-safe and the updater must be
# robust to unexpected upgrades of the system python.
#
exec /usr/bin/python $VERSIONDIR/neubot/updater/unix.py -D
