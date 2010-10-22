# neubot.nsi
# Copyright (c) 2010 NEXA Center for Internet & Society

# This file is part of Neubot.
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
# Use NSIS to create neubot installer
#

name "neubot 0.2.8"
outfile "neubot-0.2.8-setup.exe"
installdir "$PROGRAMFILES\neubot"
setcompressor lzma
section
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
    createdirectory "$SMPROGRAMS\neubot"
    createshortcut "$SMPROGRAMS\neubot\neubot (gui).lnk"		\
      "$INSTDIR\neubot-headless.exe"
    createshortcut "$SMPROGRAMS\neubot\neubot (start).lnk"		\
      "$INSTDIR\neubot-start.exe"
    createshortcut "$SMPROGRAMS\neubot\neubot (stop).lnk"		\
      "$INSTDIR\neubot-stop.exe"
    createshortcut "$SMPROGRAMS\neubot\uninstall.lnk" "$INSTDIR\uninstall.exe"
    createshortcut "$SMSTARTUP\neubot (autostart).lnk"			\
      "$INSTDIR\neubot-start.exe"
    WriteRegStr HKLM                                                    \
      "Software\Microsoft\Windows\CurrentVersion\Uninstall\neubot"      \
      "DisplayName" "neubot 0.2.8"
    WriteRegStr HKLM                                                    \
      "Software\Microsoft\Windows\CurrentVersion\Uninstall\neubot"      \
      "UninstallString" "$INSTDIR\uninstall.exe"
    exec "$INSTDIR\neubot-start.exe"
sectionend
section "uninstall"
    #
    # We cannot use neubot-stop.exe because this program does not
    # wait for neubot.exe to terminate and so there is the risk to
    # issue the remove command while the file is already locked
    # and the remove will fail.
    # To be sure that the system is not locking anymore neubot.exe
    # so that we can remove it, we sleep for a while.
    #
    execwait '"$INSTDIR\neubot.exe" stop'
    sleep 2000
    rmdir /r "$INSTDIR"
    rmdir /r "$SMPROGRAMS\neubot"
    delete "$SMSTARTUP\neubot (autostart).lnk"
    deleteregkey HKLM                                                   \
      "Software\Microsoft\Windows\CurrentVersion\Uninstall\neubot"
sectionend
