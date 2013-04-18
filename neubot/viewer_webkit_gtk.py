# neubot/viewer_webkit_gtk.py

#
# Copyright (c) 2011, 2013
#     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
#     and Simone Basso <bassosimone@gmail.com>
#
# Copyright (c) 2011 Marco Scopesi <marco.scopesi@gmail.com>
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

''' Neubot viewer using WebKit and Gtk '''

import getopt
import os.path
import sys

# If one (or both) fail, viewer.py will catch the error and
# provide a fallback main().
import gtk
import webkit

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot import utils_hier
from neubot import utils_net
from neubot import utils_rc
from neubot import utils_ctl
from neubot import utils_version

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

        self.set_title(utils_version.PRODUCT)
        self.connect('destroy', gtk.main_quit)
        self.maximize()
        self._open_web_page(uri)

        self.show_all()

    def _open_web_page(self, uri):
        ''' Open the specified web page '''
        self._webview.open(uri)

def main(args):

    ''' Entry point for simple gtk+webkit GUI '''

    try:
        _, arguments = getopt.getopt(args[1:], '')
    except getopt.error:
        sys.exit('Usage: neubot viewer')
    if arguments:
        sys.exit('Usage: neubot viewer')

    conf = utils_rc.parse_safe(utils_hier.APIFILEPATH)
    address = conf.get('address', '127.0.0.1')
    port = conf.get('port', 9774)

    uri = STATIC_PAGE
    if utils_ctl.is_running(address, port):
        uri = 'http://%s/' % utils_net.format_epnt((address, port))

    if not 'DISPLAY' in os.environ:
        sys.exit('FATAL: No DISPLAY available')
    else:
        WebkitGUI(uri)
        gtk.main()

if __name__ == '__main__':
    main(sys.argv)
