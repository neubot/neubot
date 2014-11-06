# mod_library_net/net/stream_model.py

#
# Copyright (c) 2010-2012, 2014
#   Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
#   and Simone Basso <bassosimone@gmail.com>.
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

""" Common model for TCP and SSL streams """

SUCCESS, ERROR, WANT_READ, WANT_WRITE, CONNRESET = range(5)

class StreamModel(object):
    """ Common model for TCP and SSL streams """

    def __init__(self, sock):
        self.sock = sock

    def soclose(self):
        """ Close the stream """

    def sorecv(self, maxrecv):
        """ Receive data from the stream """

    def sosend(self, octets):
        """ Send data over the stream """
