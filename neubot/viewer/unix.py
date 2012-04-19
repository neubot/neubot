# neubot/viewer/unix.py

#
# Copyright (c) 2011 Marco Scopesi <marco.scopesi@gmail.com>,
#  Politecnico di Torino
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

''' Neubot GUI '''

import getopt
import os.path
import sqlite3
import sys
import time

if sys.version_info[0] == 3:
    import http.client as lib_http
else:
    import httplib as lib_http

try:
    import gtk
    import webkit
except ImportError:
    sys.exit('Viewer support not available.')

ICON = '@DATADIR@/icons/hicolor/scalable/apps/neubot.svg'
if not os.path.isfile(ICON) or not os.access(ICON, os.R_OK):
    ICON = None

STATIC_PAGE = '@DATADIR@/neubot/www/not_running.html'
if STATIC_PAGE.startswith('@DATADIR@'):
    STATIC_PAGE = os.path.abspath(STATIC_PAGE.replace('@DATADIR@', '.'))

class WebkitGUI(gtk.Window):

    ''' Webkit- and Gtk-based GUI '''

    def __init__(self, uri):

        ''' Initialize the window '''

        gtk.Window.__init__(self)

        scrolledwindow = gtk.ScrolledWindow()
        self._webview = webkit.WebView()
        scrolledwindow.add(self._webview)
        self.add(scrolledwindow)

        if ICON:
            self.set_icon_from_file(ICON)

        self.set_title('Neubot 0.4.11-rc5')
        self.connect('destroy', gtk.main_quit)
        self.maximize()
        self._open_web_page(uri)

        self.show_all()

    def _open_web_page(self, uri):
        ''' Open the specified web page '''
        self._webview.open(uri)

def __is_running(address, port):

    ''' Returns True if Neubot is running '''

    #
    # When there is a huge database upgrade Neubot may take
    # time to start.  For this reason here we retry and wait
    # for a number of seconds before giving up.
    #

    for _ in range(15):
        running = False

        try:

            connection = lib_http.HTTPConnection(address, port)
            connection.request("GET", "/api/version")
            response = connection.getresponse()
            if response.status == 200:
                running = True

            response.read()
            connection.close()

        except (SystemExit, KeyboardInterrupt):
            raise
        except:
            pass

        if running:
            return True

        time.sleep(1)

    return False

def main(args):

    ''' Entry point for simple gtk+webkit GUI '''

    try:
        options, arguments = getopt.getopt(args[1:], 'f:')
    except getopt.error:
        sys.exit('Usage: neubot viewer [-f database]')
    if arguments:
        sys.exit('Usage: neubot viewer [-f database]')

    database = '/var/neubot/database.sqlite3'
    for name, value in options:
        if name == '-f':
            database = value

    address, port = '127.0.0.1', '9774'
    connection = sqlite3.connect(database)
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM config;')
    for name, value in cursor:
        if name == 'agent.api.address':
            address = value
        elif name == 'agent.api.port':
            port = value
    connection.close()

    uri = STATIC_PAGE
    if __is_running(address, port):
        uri = 'http://%s:%s/' % (address, port)

    if not 'DISPLAY' in os.environ:
        sys.exit('No DISPLAY available')
    else:
        WebkitGUI(uri)
        gtk.main()

if __name__ == '__main__':
    main(sys.argv)
