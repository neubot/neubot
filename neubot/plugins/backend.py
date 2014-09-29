#
# This file is part of Neubot <http://www.neubot.org/>.
#
# Neubot is free software. See AUTHORS and COPYING for more
# information on the copying conditions.
#

""" Propagates the result of a test to the parent process """

import json
import sys

class BackendStdout(object):
    """ Passed to plugins as BACKEND """

    def bittorrent_store(self, message):
        """ Save result of BitTorrent test """
        self.store_generic("bittorrent", message)

    def store_raw(self, message):
        """ Save result of RAW test """
        self.store_generic("raw", message)

    def speedtest_store(self, message):
        """ Save result of speedtest test """
        self.store_generic("speedtest", message)

    @staticmethod
    def store_generic(test, results):
        """ Store the results of a generic test """
        sys.stdout.write("=== BEGIN TEST RESULT ===\n")
        sys.stdout.write("%s\n" % json.dumps({
            "test": test,
            "results": results,
        }, indent=4))
        sys.stdout.write("=== END TEST RESULT ===\n")
