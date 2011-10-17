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

''' Initialize and manage privacy settings '''

import asyncore
import getopt
import os
import sqlite3
import sys
import types
import xml.dom.minidom

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot.config import CONFIG
from neubot.config import ConfigError
from neubot.log import LOG
from neubot.database import table_config
from neubot import rootdir
from neubot import utils

def check(updates):

    ''' Raises ConfigError if the user is trying to update the
        privacy settings in a wrong way '''

    conf = CONFIG.copy()

    conf.update(updates)

    informed = utils.intify(conf['privacy.informed'])
    can_collect = utils.intify(conf['privacy.can_collect'])

    if not (informed == can_collect == 1):
        raise ConfigError(
'Invalid privacy configuration: (i) you must be informed and (ii) Neubot '
'cannot work if it cannot collect your Internet address.  If that is a '
'problem for you, either disable Neubot or uninstall it.')

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

def allowed_to_run():
    ''' Returns True if the user is informed and has
        provided the permission to collect '''
    return utils.intify(CONFIG['privacy.informed']) and \
      utils.intify(CONFIG['privacy.can_collect'])

def complain():
    ''' Complain with the user about privacy settings '''
    LOG.warning('Neubot is disabled because privacy settings are not OK.')
    LOG.warning('Please, set privacy settings via web user interface.')
    LOG.warning('Alternatively, you can use the `neubot privacy` command.')

def complain_if_needed():
    ''' Complain with the user if privacy settings are not OK '''
    if not allowed_to_run():
        complain()

USAGE = '''
Usage: neubot privacy [-P] [-D name=value] [-f database]

Options:
    -D name=value       : Set privacy setting value
    -f database         : Force database path
    -P                  : Print privacy policy on stdout

Settings:
    privacy.informed    : You have read Neubot's privacy policy
    privacy.can_collect : Neubot can save your IP address
    privacy.can_share   : Neubot can publish your IP address

Neubot does not work unless you assert that you are informed and
you provide the permission to collect.
'''

POLICY = os.sep.join([rootdir.WWW, 'privacy.html'])

def main(args):

    ''' Wrapper for the real main '''

    try:
        __main(args)
    except (SystemExit, KeyboardInterrupt):
        raise
    except:
        sys.stderr.write('ERROR: unhandled exception: %s\n' %
           str(asyncore.compact_traceback()))
        sys.exit(1)

def __main(args):

    ''' Initialize privacy settings '''

    try:
        options, arguments = getopt.getopt(args[1:], 'D:f:P')
    except getopt.error:
        sys.exit(USAGE)
    if arguments:
        sys.exit(USAGE)

    settings = {}
    database_path = '/var/neubot/database.sqlite3'
    pflag = False
    for name, value in options:
        if name == '-D':
            name, value = value.split('=', 1)
            settings[name] = value
        elif name == '-f':
            database_path = value
        elif name == '-P':
            pflag = True

    if pflag:
        filep = open(POLICY, 'rb')
        body = ''.join([ '<HTML>', filep.read(), '</HTML>' ])
        filep.close()
        document = xml.dom.minidom.parseString(body)
        for element in document.getElementsByTagName('textarea'):
            if element.getAttribute('class') != 'i18n i18n_privacy_policy':
                continue
            element.normalize()
            for node in element.childNodes:
                if node.nodeType == node.TEXT_NODE:
                    for line in node.data.splitlines():
                        sys.stdout.write(line.strip())
                        sys.stdout.write('\n')
                    sys.exit(0)
        sys.stderr.write('ERROR cannot extract policy from privacy.html\n')
        sys.exit(1)
    else:

        connection = sqlite3.connect(database_path)
        if settings:
            # Just in case...
            table_config.create(connection)
            for name, value in settings.items():
                if name not in ('privacy.informed', 'privacy.can_collect',
                            'privacy.can_share'):
                    sys.stderr.write('WARNING unknown setting: %s\n' % name)
                    del settings[name]
            table_config.update(connection, settings.items())
            # Live with that or provide a patch
            sys.stdout.write('*** Database changed.  Please, restart Neubot.\n')
        else:

            sys.stdout.write(USAGE + '\n')
            sys.stdout.write('Current database: %s\n' % database_path)
            sys.stdout.write('Current settings:\n')
            cursor = connection.cursor()
            cursor.execute('SELECT * FROM config;')
            for name, value in cursor:
                if name.startswith('privacy.'):
                    sys.stdout.write('    %-20s: %d\n' % (name,
                            utils.intify(value)))
            sys.stdout.write('\n')

if __name__ == '__main__':
    main(sys.argv)
