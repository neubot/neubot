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
# 1) We know what files we should install and the comparison
# with that also allow to say that Makefile honours all
# variables and allow the package the tweak the installation.
#
# 2) We also grep the installer sources for @SOMETHING@ variables
# to be sure that we don't install stuff with placeholders.
#
# 3) We also make sure that we do not install more executable
#    files than needed.
#

set -e

#
# Make sure sorting is stable across operating systems
# that have different defaults
#
export LC_COLLATE=C

make clean
make -f Makefile _install DESTDIR=dist/temp SYSCONFDIR=/sysconfdir \
    LOCALSTATEDIR=/localstatedir BINDIR=/bindir DATADIR=/datadir \
    MANDIR=/mandir

# 1)
find dist/temp | sort > regress/Makefile/install.new
diff -u regress/Makefile/install.txt regress/Makefile/install.new

# 2)
grep -RnE '@[A-Z]+@' dist/temp && exit 1

# 3)
find dist/temp -perm -0111 -type f | sort \
	> regress/Makefile/install.exec.new
diff -u regress/Makefile/install.exec.txt regress/Makefile/install.exec.new
find dist/temp ! -perm -0111 -type f | sort \
	> regress/Makefile/install.noexec.new
diff -u regress/Makefile/install.noexec.txt regress/Makefile/install.noexec.new

echo ''
echo '*** Success: `make install` works as expected'
