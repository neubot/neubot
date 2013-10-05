# neubot/backend_volatile.py

#
# Copyright (c) 2013
#     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN),
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

""" The volatile backend """

from neubot.backend_null import BackendNull

class BackendVolatile(BackendNull):
    """ The volatile backend """
    # Adapted from neubot/backend_neubot.py

    def __init__(self, proxy):
        BackendNull.__init__(self, proxy)
        self.generic = {}

    def store_generic(self, test, results):
        """ Store the results of a generic test """
        self.generic.setdefault(test, [])
        self.generic[test].append(results)

    def walk_generic(self, test, index):
        """ Walk over the results of a generic test """
        return self.generic.get(test, [])
