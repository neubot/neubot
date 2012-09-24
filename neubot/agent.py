# neubot/agent.py

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

''' Agent command '''

#
# This module is being decommissioned, and will be replaced by
# the family of background_foo.py modules.  At the moment
# just Neubot for win32 is using background_win32.py and this
# module is still being used on MacOSX and POSIX.
#

import sys
import logging

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.http.server import HTTP_SERVER
from neubot.api.server import ServerAPI
from neubot.background_rendezvous import BACKGROUND_RENDEZVOUS
from neubot.net.poller import POLLER

from neubot.config import CONFIG
from neubot.database import DATABASE
from neubot.log import LOG
from neubot.main import common

from neubot import privacy
from neubot import system
from neubot import utils_sysdirs

def main(args):
    """ Main function """

    common.main("agent", "Run in background, periodically run tests", args)

    conf = CONFIG.copy()

    privacy.complain_if_needed()

    if conf["agent.api"]:
        server = HTTP_SERVER
        logging.debug("* API server root directory: %s", utils_sysdirs.WWWDIR)
        conf["http.server.rootdir"] = utils_sysdirs.WWWDIR
        conf["http.server.ssi"] = True
        conf["http.server.bind_or_die"] = True
        server.configure(conf)
        server.register_child(ServerAPI(POLLER), "/api")
        server.listen((conf["agent.api.address"],
                       conf["agent.api.port"]))

    if conf["agent.daemonize"]:
        system.change_dir()
        system.go_background()
        system.write_pidfile()
        LOG.redirect()

    if conf["agent.use_syslog"]:
        LOG.redirect()

    system.drop_privileges()

    #
    # When we run as an agent we also save logs into
    # the database, to easily access and show them via
    # the web user interface.
    #
    LOG.use_database()

    if conf["agent.rendezvous"]:
        BACKGROUND_RENDEZVOUS.start()

    POLLER.loop()

    #
    # Make sure that we do not leave the database
    # in an inconsistent state.
    #
    DATABASE.close()

if __name__ == "__main__":
    main(sys.argv)
