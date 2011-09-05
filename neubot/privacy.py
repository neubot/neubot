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

'''
 Initialize and manage privacy settings
'''

import types
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot.config import CONFIG
from neubot.config import ConfigError
from neubot.log import LOG

from neubot.database import table_config
from neubot.database import DATABASE
from neubot.main import common

from neubot import utils

PRIVACYKEYS = (
               "privacy.informed",
               "privacy.can_collect",
               "privacy.can_share"
              )

def check(updates):

    ''' Raises ConfigError if the user is trying to update the
        privacy settings in a wrong way '''

    # Merge a copy of config with privacy settings
    conf = CONFIG.copy()
    for key in PRIVACYKEYS:
        if key in updates:
            conf[key] = utils.intify(updates[key])

    # Extract privacy settings from such copy
    informed = utils.intify(conf.get("privacy.informed", 0))
    can_collect = utils.intify(conf.get("privacy.can_collect", 0))
    can_share = utils.intify(conf.get("privacy.can_share", 0))

    if not informed:

        # When you're not informed you cannot raise the other settings
        if can_collect or can_share:
            raise ConfigError("You cannot set can_collect or can_share "
                             "without asserting that you are informed")

    else:

        # It's not possible to share if you don't agree to collect
        if can_share and not can_collect:
            raise ConfigError("You cannot set can_share without also "
                             "setting can_collect (how are we supposed "
                             "to share what we cannot collect)?")

        # You must give the can_collect bit
        if not can_collect:
            raise ConfigError("You must agree to collect or Neubot "
                              "cannot work.  You should uninstall Neubot "
                              "if you don't want it to collect")

    # You cannot remove the informed bit
    if utils.intify(CONFIG['privacy.informed']) and not informed:
        raise ConfigError("Once you're informed you cannot step back")

    # You cannot remove the can_collect bit
    if utils.intify(CONFIG['privacy.can_collect']) and not can_collect:
        raise ConfigError("You can't remove the can_collect bit because "
                          "Neubot cannot work.  You should uninstall Neubot "
                          "if you don't want it to collect")

def collect_allowed(m):

    ''' Returns True if we are allowed to collect a result into the
        database, and False otherwise '''

    if type(m) != types.DictType:
        #
        # XXX This is a shame therefore put the oops() and hope that
        # it does its moral suasion job as expected.
        #
        LOG.oops("TODO: please pass me a dictionary!", LOG.debug)
        m = m.__dict__
    return (not utils.intify(m["privacy_informed"])
            or utils.intify(m["privacy_can_collect"]))

CONFIG.register_defaults({
                          'privacy.init_informed': 0,
                          'privacy.init_can_collect': 0,
                          'privacy.init_can_share': 0,
                          'privacy.overwrite': 0,
                         })

def main(args):

    ''' Will initialize privacy settings '''

    CONFIG.register_descriptions({
        'privacy.init_informed': "You've read privacy policy",
        'privacy.init_can_collect': 'We can collect your IP address',
        'privacy.init_can_share': 'We can share your IP address',
        'privacy.overwrite': 'Overwrite old settings',
                                 })

    common.main('privacy', 'Initialize privacy settings', args)
    conf = CONFIG.copy()

    if not conf['privacy.informed'] or conf['privacy.overwrite']:
        dictonary = {
                     'privacy.informed': conf['privacy.init_informed'],
                     'privacy.can_collect': conf['privacy.init_can_collect'],
                     'privacy.can_share': conf['privacy.init_can_share'],
                    }
        table_config.update(DATABASE.connection(), dictonary.iteritems())

    DATABASE.connection().commit()

if __name__ == '__main__':
    main(sys.argv)
