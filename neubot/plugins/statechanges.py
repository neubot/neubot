#
# This file is part of Neubot <http://www.neubot.org/>.
#
# Neubot is free software. See AUTHORS and COPYING for more
# information on the copying conditions.
#

""" Propagates state changes to the parent process """

import sys

class ForwardStateChanges(object):
    """ Passed to plugins as STATE and NOTIFIER """

    def __init__(self, poller):
        self._poller = poller

    @staticmethod
    def update(name, event=None, publish=True):
        """ Updates the test state """
        if not event:
            event = {}
        sys.stdout.write("state: %s %s\n" % (name, event))
        if not publish:
            return
        sys.stdout.write("---\n")
        sys.stdout.flush()

    def publish(self, name):
        """ Publishes global state changes """
        sys.stdout.write("notify: %s\n" % name)
        sys.stdout.write("---\n")
        sys.stdout.flush()
        if name == "testdone":
            self._poller.break_loop()
