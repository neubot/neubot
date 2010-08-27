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

name "Network Neutrality Bot (Neubot) 0.2.1"
outfile "Neubot_Setup_0.2.1.exe"
installdir "$PROGRAMFILES\Neubot"
section
    setoutpath "$INSTDIR"
    file "dist\*.*"
    writeuninstaller "$INSTDIR\uninstall.exe"
    createdirectory "$SMPROGRAMS\Neubot"
    createshortcut "$SMPROGRAMS\Neubot\neubot.lnk" "$INSTDIR\neubot.exe"
    createshortcut "$SMPROGRAMS\Neubot\uninstall.lnk" "$INSTDIR\uninstall.exe"
    WriteRegStr HKLM                                                    \
      "Software\Microsoft\Windows\CurrentVersion\Uninstall\Neubot"      \
      "DisplayName" "Neubot"
    WriteRegStr HKLM                                                    \
      "Software\Microsoft\Windows\CurrentVersion\Uninstall\Neubot"      \
      "UninstallString" "$INSTDIR\uninstall.exe"
sectionend
section "uninstall"
    rmdir /r "$INSTDIR"
    rmdir /r "$SMPROGRAMS\Neubot"
    deleteregkey HKLM                                                   \
      "Software\Microsoft\Windows\CurrentVersion\Uninstall\Neubot"
sectionend
