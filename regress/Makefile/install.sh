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
# We know what files we should install and the comparison
# with that also allow to say that Makefile honours all
# variables and allow the package the tweak the installation.
#
# We also grep the installer sources for @SOMETHING@ variables
# to be sure that we don't install stuff with placeholders.
#

set -e

make clean
make -f Makefile _install DESTDIR=dist/temp SYSCONFDIR=/sysconfdir \
    LOCALSTATEDIR=/localstatedir BINDIR=/bindir DATADIR=/datadir \
    MANDIR=/mandir
find dist/temp | sort > regress/Makefile/install.new
diff -u regress/Makefile/install.txt regress/Makefile/install.new
grep -RnE '@[A-Z]+@' dist/temp && exit 1

echo ''
echo '*** Success: `make install` works as expected'
