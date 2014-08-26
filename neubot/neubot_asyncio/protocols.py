#
# This file is part of Neubot <http://www.neubot.org/>.
#
# Neubot is free software. See AUTHORS and COPYING for more
# information on the copying conditions.
#

# pylint: disable = missing-docstring

class _Protocol(object):

    def connection_made(self, transport):
        pass

    def connection_lost(self, error):
        pass

    def pause_writing(self):
        pass

    def resume_writing(self):
        pass

    def data_received(self, data):
        pass

    def eof_received(self):
        pass
