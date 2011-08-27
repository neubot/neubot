#!/bin/sh

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
# cmdline.sh -- Access neubot(1) via command line.
#
# We install a symlink from /usr/local/bin/neubot to this file
# which just invokes Neubot main() passing it all arguments.
#

#
# We're a link to a file in the proper directory so just read
# the link and then we can do the now usual dirname trick.
#
VERSIONDIR=$(dirname $(readlink $0))

# Jump the the entry point
/usr/bin/python $VERSIONDIR/neubot/main/__init__.py $@
