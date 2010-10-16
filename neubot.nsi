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

name "neubot 0.2.7"
outfile "Neubot_Setup_0.2.7.exe"
installdir "$PROGRAMFILES\neubot"
section
    setoutpath "$INSTDIR"
    file /r "dist\*.*"
    writeuninstaller "$INSTDIR\uninstall.exe"
    createdirectory "$SMPROGRAMS\neubot"
    createshortcut "$SMPROGRAMS\neubot\neubot.lnk" "$INSTDIR\neubot.exe"
    createshortcut "$SMPROGRAMS\neubot\uninstall.lnk" "$INSTDIR\uninstall.exe"
    WriteRegStr HKLM                                                    \
      "Software\Microsoft\Windows\CurrentVersion\Uninstall\neubot"      \
      "DisplayName" "neubot"
    WriteRegStr HKLM                                                    \
      "Software\Microsoft\Windows\CurrentVersion\Uninstall\neubot"      \
      "UninstallString" "$INSTDIR\uninstall.exe"
sectionend
section "uninstall"
    rmdir /r "$INSTDIR"
    rmdir /r "$SMPROGRAMS\neubot"
    deleteregkey HKLM                                                   \
      "Software\Microsoft\Windows\CurrentVersion\Uninstall\neubot"
sectionend
