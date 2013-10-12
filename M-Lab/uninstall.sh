#!/bin/sh -e

#
# Copyright (c) 2013
#     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
#     and Simone Basso <bassosimone@gmail.com>
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
# Uninstall Neubot from M-Lab sliver - Invoked on the sliver
# by init/initialize.sh.
#
# I want this script to run before installing a new Neubot to make sure that
# the previous version sources are removed: keeping around old source files
# removed from current version may cause random bugs.
#
# I don't remove the user and the group, though, because I
# never uninstall Neubot from M-Lab without immediately installing
# a newer version.
#

DEBUG=
$DEBUG echo "remove old neubot sources"
$DEBUG rm -rf /home/mlab_neubot/neubot
