# neubot/privacy.py

#
# Copyright (c) 2011, 2013
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

''' Initialize and manage privacy settings '''

import getopt
import os
import sys
import xml.dom.minidom
import logging

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot.config import CONFIG
from neubot.config import ConfigError
from neubot.database import table_config
from neubot.database import DATABASE

from neubot import utils_hier
from neubot import system
from neubot import utils

def count_valid(updates, prefix):

    ''' Return the number of valid privacy settings found
        and return -1 in case of error '''

    count = 0
    for setting in ('informed', 'can_collect', 'can_publish'):
        name = "%s%s" % (prefix, setting)
        if name in updates:
            value = utils.intify(updates[name])
            if not value:
                return -1
            count += 1
    return count

def check(updates, check_all=False, prefix='privacy.'):

    ''' Raises ConfigError if the ``updates`` dictionary does not
        contain valid privacy settings '''

    count = count_valid(updates, prefix)
    if count < 0:
        raise ConfigError(
'Invalid privacy settings.  Neubot is not allowed to use the distributed '
'M-Lab platform to perform tests unless you (i) assert that you have '
'read the privacy policy and you provide the permission to (ii) collect '
'and (iii) publish your Internet address.')

    elif check_all and count != 3:
        raise ConfigError('Not all privacy settings were specified')

def collect_allowed(message):

    ''' We are allowed to collect a result in the database if the
        user is informed and has provided the permission to collect
        her Internet address '''

    return (utils.intify(message['privacy_informed']) and
            utils.intify(message['privacy_can_collect']))

def allowed_to_run():
    ''' We are allowed to run if and only if we have all permissions '''

    return (count_valid(CONFIG.conf, prefix='privacy.') == 3)

def complain():
    ''' Complain with the user about privacy settings '''
    logging.warning('Neubot is disabled because privacy settings are not OK.')
    logging.warning('Please, set privacy settings via web user interface.')
    logging.warning('Alternatively, you can use the `neubot privacy` command.')

def complain_if_needed():
    ''' Complain with the user if privacy settings are not OK '''
    if not allowed_to_run():
        complain()

USAGE = '''usage: neubot privacy [-Pt] [-D setting=value] [-f database]'''

POLICY = os.sep.join([utils_hier.WWWDIR, 'privacy.html'])

def main(args):

    ''' Wrapper for the real main '''

    try:
        __main(args)
    except (SystemExit, KeyboardInterrupt):
        raise
    except:
        logging.error('unhandled exception\n', exc_info=1)
        sys.exit(1)

def print_policy():

    ''' Print privacy policy and exit '''

    filep = open(POLICY, 'rb')
    body = ''.join([ '<HTML>', filep.read(), '</HTML>' ])
    filep.close()

    # Adapted from scripts/make_lang_en.py
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
                return 0

    sys.stderr.write('ERROR cannot extract policy from privacy.html\n')
    return 1

def test_settings(connection):

    ''' Test privacy settings and exit, setting properly the
        exit value '''

    settings = table_config.dictionarize(connection)
    if count_valid(settings, 'privacy.') == 3:
        return 0

    return 1

def update_settings(connection, settings):

    ''' Update database privacy settings and exit '''

    for name in settings.keys():
        if name not in ('privacy.informed', 'privacy.can_collect',
                    'privacy.can_publish'):
            sys.stderr.write('WARNING unknown setting: %s\n' % name)
            del settings[name]
    table_config.update(connection, settings.items())
    # Live with that or provide a patch
    sys.stdout.write('*** Database changed.  Please, restart Neubot.\n')

    return 0

def print_settings(connection, database_path):

    ''' Print privacy settings and exit '''

    sys.stdout.write('database: %s\n' % database_path)
    sys.stdout.write('settings:\n')
    dictionary = table_config.dictionarize(connection)
    for name, value in dictionary.items():
        if name.startswith('privacy.'):
            name = name.replace("privacy.", "")
            sys.stdout.write('    %-12s: %d\n' % (name,
                    utils.intify(value)))
    sys.stdout.write('\n')

    return 0

def __main(args):

    ''' Initialize privacy settings '''

    try:
        options, arguments = getopt.getopt(args[1:], 'D:f:Pt')
    except getopt.error:
        sys.exit(USAGE)
    if arguments:
        sys.exit(USAGE)

    settings = {}
    database_path = system.get_default_database_path()
    pflag = False
    testmode = False
    for name, value in options:
        if name == '-D':
            name, value = value.split('=', 1)
            if not name.startswith("privacy."):
                name = "privacy." + name
            settings[name] = value
        elif name == '-f':
            database_path = value
        elif name == '-P':
            pflag = True
        elif name == '-t':
            testmode = True

    if pflag:
        sys.exit(print_policy())

    DATABASE.set_path(database_path)
    connection = DATABASE.connection()

    if testmode:
        sys.exit(test_settings(connection))

    if settings:
        if DATABASE.readonly:
            sys.exit('ERROR: readonly database')
        sys.exit(update_settings(connection, settings))

    sys.exit(print_settings(connection, database_path))

if __name__ == '__main__':
    main(sys.argv)
