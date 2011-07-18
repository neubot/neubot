# neubot/system/_proc_win32.py

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
# =================================================================
# The _kill_pid() function is a derivative work of the code
# by Jimmy Retziaff released under the Python Sofware Foundation
# License, see http://bit.ly/qEqaIa [code.activestate.com].
#
# I've put a copy of Python LICENSE file at doc/LICENSE.Python.
# -----------------------------------------------------------------
# The __list_procs() function is written from scratch but
# based on the recipe posted by Roger Upole on the python-win32
# mailing list, see http://bit.ly/mPEFZ0 [mail.python.org].
# =================================================================
#

#
# No public functions in this file because we have yet
# to agree a common API to walk the list of running procs
# on different platforms.
#

import win32com.client
import win32api

__PROCESS_TERMINATE = 1

def __list_procs():
    """Return (NAME, PID) of all the running processes"""
    wmi = win32com.client.GetObject('winmgmts:')
    return ((p.name, p.Properties_('ProcessId'))
            for p in wmi.InstancesOf('win32_process'))

def __walk_procs(func):
    """Invoke FUNC on each running process"""
    map(func, __list_procs())

# Kill the process using pywin32 and pid
def _kill_pid(pid):
    """Given the process PID, kill the process."""
    handle = win32api.OpenProcess(__PROCESS_TERMINATE, False, pid)
    win32api.TerminateProcess(handle, -1)
    win32api.CloseHandle(handle)

def _kill_process(name):
    """Kill all the instances of the process given by NAME."""

    def __killer(tpl):
        if tpl[0] == name:
            _kill_pid(tpl[1])

    __walk_procs(__killer)
