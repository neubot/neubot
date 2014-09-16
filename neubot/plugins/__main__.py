#
# This file is part of Neubot <http://www.neubot.org/>.
#
# Neubot is free software. See AUTHORS and COPYING for more
# information on the copying conditions.
#

""" Neubot plugins main(). """

import getopt
import pprint
import sys

from neubot.backend import BACKEND
from neubot.config import CONFIG
from neubot import log
from neubot.http.server import HTTP_SERVER
from neubot.negotiate.server import NEGOTIATE_SERVER
from neubot.notify import NOTIFIER
from neubot.poller import POLLER
from neubot import log

from . import common

USAGE = """usage: neubot plugins [-cNv] [-D key=value] name"""

def main(args):
    """ Main function """

    try:
        options, arguments = getopt.getopt(args[1:], "cD:lNv")
    except getopt.error:
        sys.exit(USAGE)
    if len(arguments) != 1:
        sys.exit(USAGE)

    only_check = False
    listen = False
    negotiate = False
    params = {}

    for name, value in options:
        if name == "-c":
            only_check = True
        elif name == "-D":
            pname, pvalue = value.split("=", 1)
            params[pname] = pvalue
        elif name == "-l":
            listen = True
        elif name == "-N":
            negotiate = True
        elif name == "-v":
            log.set_verbose()

    spec = common.probe_plugin(arguments[0])

    if only_check:
        pprint.pprint(spec)
        sys.exit(0)

    BACKEND.use_backend("volatile")

    if listen:
        if negotiate:
            common.run_testcontroller_server(spec, params)

            # Magic code to setup the base negotiate server
            conf = CONFIG.copy()
            conf["http.server.rootdir"] = ""
            HTTP_SERVER.configure(conf)
            HTTP_SERVER.listen(("127.0.0.1", 8080))
            HTTP_SERVER.register_child(NEGOTIATE_SERVER, "/negotiate")
            HTTP_SERVER.register_child(NEGOTIATE_SERVER, "/collect")

        else:
            common.run_testprovider_server(spec, params)
    else:
        if negotiate:
            common.run_testcontroller_client(spec, params)
        else:
            common.run_testprovider_client(spec, params)

    NOTIFIER.subscribe("testdone", lambda *args: POLLER.break_loop())
    POLLER.loop_forever()

if __name__ == "__main__":
    main(sys.argv)
