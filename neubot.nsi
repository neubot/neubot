# neubot.nsi

#
# Copyright (c) 2010-2011 Simone Basso <bassosimone@gmail.com>,
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

name "neubot 0.4.3-rc4"
outfile "neubot-0.4.3-rc4-setup.exe"
installdir "$PROFILE\Neubot"
setcompressor lzma
requestexecutionlevel user

section

    # Cannot uninstall Neubot <= 0.4.2
    iffileexists "$PROGRAMFILES\neubot\uninstall.exe" 0 +3
        messagebox MB_OK 'Detected an old version of Neubot.  Please uninstall it manually.$\nThis installer runs with user privileges and cannot uninstall it automatically.'
        quit

    #
    # If a previous version is already installed uninstall it. We need
    # to pass uninstall.exe the magic argument below otherwise execwait
    # will not wait for the uninstaller (see NSIS wiki).
    # To be sure that the system is not locking anymore uninstall.exe
    # so that we can overwrite it, we sleep for a while.
    #
    iffileexists "$INSTDIR\uninstall.exe" 0 +3
        execwait '"$INSTDIR\uninstall.exe" _?=$INSTDIR'
        sleep 2000

    setoutpath "$INSTDIR"
    file /r "dist\*.*"
    writeuninstaller "$INSTDIR\uninstall.exe"

    createshortcut "$SMPROGRAMS\Neubot.lnk" "$INSTDIR\neubotw.exe"
    createshortcut "$SMSTARTUP\Neubot.lnk" "$INSTDIR\neubotw.exe" "start"

    WriteRegStr HKLM                                                    \
      "Software\Microsoft\Windows\CurrentVersion\Uninstall\Neubot"      \
      "DisplayName" "Neubot 0.4.3-rc4"
    WriteRegStr HKLM                                                    \
      "Software\Microsoft\Windows\CurrentVersion\Uninstall\Neubot"      \
      "UninstallString" "$INSTDIR\uninstall.exe"

    exec '"$INSTDIR\neubotw.exe" start'

sectionend

section "uninstall"

    execwait '"$INSTDIR\neubotw.exe" stop'

    #
    # To be sure that the system is not locking anymore neubotw.exe
    # so that we can remove it, we sleep for a while.
    #
    sleep 2000

    rmdir /r "$INSTDIR"
    delete "$SMPROGRAMS\Neubot.lnk"
    delete "$SMSTARTUP\Neubot.lnk"

    deleteregkey HKLM                                                   \
      "Software\Microsoft\Windows\CurrentVersion\Uninstall\Neubot"

sectionend
