# neubot/viewer/__init__.py

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

''' The viewer is the component of Neubot that allows the user to
    view the current state of the daemon and recent results.  To do
    that, it embeds the web browser into a graphical frame, using
    the most convenient toolkit for the platform. '''

import os
import sys

if os.name == 'posix' and sys.platform != 'darwin':
    from neubot.viewer_webkit_gtk import main
else:
    def main(args):
        ''' main stub '''
        sys.exit('Viewer not implemented on this platform.')
