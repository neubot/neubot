# neubot/privacy.py

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

from neubot.config import CONFIG
from neubot.config import ConfigError
from neubot import utils

PRIVACYKEYS = ("privacy.informed", "privacy.can_collect",
               "privacy.can_share")

def check(updates):
    conf = CONFIG.copy()
    for key in PRIVACYKEYS:
        if key in updates:
            conf[key] = utils.intify(updates[key])
    informed = conf.get("privacy.informed", 0)
    can_collect = conf.get("privacy.can_collect", 0)
    can_share = conf.get("privacy.can_share", 0)
    if not informed:
        if can_collect or can_share:
            raise ConfigError("You cannot set can_collect or can_share "
                             "without asserting that you are informed")
    else:
        if can_share and not can_collect:
            raise ConfigError("You cannot set can_share without also "
                             "setting can_collect (how are we supposed "
                             "to share what we cannot collect)?")
