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
# start.sh -- Start neubotd(1) under MacOSX
#
# Lookup the most recent version of Neubot that has been
# installed below /usr/local/share/neubot (aka BASEDIR)
# and then starts Neubot in foreground, using exec to replace
# the current process image with a new image.  This is
# important because we assume that we're started by launchd(8),
# so we must not exit and we must not go background.
#
# Below BASEDIR there is a directory for each available
# version of Neubot.  Each of this directories is a VERSIONDIR
# because it holds a specific version of the software.  The
# VERSIONDIRs are named after the *numeric* representation
# of the current version number, which is basically a floating
# point with nine digits after the radix point.  Hence the
# comparison is just a matter of invoking `sort -rn`.  As an
# example of numeric representation, version 0.3.7 is represented
# as 0.003007999 -- where 999 is the release candidate number
# and 999 means "this not a candidate, this is stable".
#
# Before trusting a given VERSIONDIR we need to make sure
# that it is *valid*.  In other words that all the content
# that should have been written into it has actually been
# written.  A VERSIONDIR is valid if it contains the so-called
# OKFILE (`.neubot-installed-ok`).  The rationale is: when
# we'll have automatic updates and we start an update it is
# possible for an update to be in progress while the user
# is switching off her computer.  In this case not all the
# files may be written and, as a result, that version of
# Neubot will not work.  So, the installer must write such
# OKFILE when *sure* that the installation completed
# cleanly.  Of course, there is always a clean version,
# i.e. the one installed at hand by the user.
#

set -e

OKFILE=.neubot-installed-ok
BASEDIR=/usr/local/share/neubot/

cd $BASEDIR

for CANDIDATE in $(ls|sort -rn); do

	# Not a directory
	if ! [ -d $CANDIDATE ]; then
		continue
	fi

	# Not installed cleanly
	if ! [ -f $CANDIDATE/$OKFILE ]; then
		continue
	fi

	VERSIONDIR=$BASEDIR/$CANDIDATE

	#
	# Hand-over the control to a per-Neubot version
	# script that actually starts the daemon.  The
	# rationale is that each version knows the path
	# of the main.py file and what checks to perform
	# before invoking it.  For example, a new version
	# might need to check and possibly create a new
	# unprivileged user and so on and so forth.
        #
	# Invoke the child process using an absolute
	# path so that it can easily get the base path
	# where we are installed via dirname.
	#
	exec $VERSIONDIR/start.sh

done

# Should not happen
logger -p daemon.error -t $0 'No candidate Neubot'
exit 1
