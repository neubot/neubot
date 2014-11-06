# mod_dash/server/test_provider_glue.py

#
# Copyright (c) 2010-2014
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

""" MPEG DASH server glue """

# Adapted from neubot/raw_srvr_glue.py

from .test_provider import TestProviderServer

class TestProviderServerGlue(TestProviderServer):
    """ Glue for DASH on the server side """

    def __init__(self, poller, negotiator):
        TestProviderServer.__init__(self, poller)
        self.negotiator = negotiator

    def got_request_headers(self, stream, request):
        """ Filter incoming HTTP requests """

        if self.negotiator:
            auth = request["Authorization"]
            if not auth:
                return False

            if auth not in self.negotiator.peers:
                return False

        return TestProviderServer.got_request_headers(self, stream, request)
