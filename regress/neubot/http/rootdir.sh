#!/bin/sh -e

#
# Copyright (c) 2012 Simone Basso <bassosimone@gmail.com>,
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
# Regression test that checks whether http.server.rootdir statu quo
# changes.  This is a critical setting and I want to give myself a
# second chance of catching and reflecting on changes at it.
#

# Make sure there are no *.pyc files around
make clean

#
# Make sure sorting is stable across operating systems
# that have different defaults
#
export LC_COLLATE=C

grep -R http.server.rootdir neubot | sort > \
  regress/neubot/http/rootdir.txt.new
diff -u regress/neubot/http/rootdir.txt \
  regress/neubot/http/rootdir.txt.new
