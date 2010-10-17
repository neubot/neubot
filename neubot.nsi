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
outfile "neubot-0.2.7-setup.exe"
installdir "$PROGRAMFILES\neubot"
setcompressor lzma
section
    #
    # XXX It's not very clean to blindly execute neubot.exe because
    # neubot might not be installed, but luckily NSIS allows that :).
    # XXX The original idea here was to (blindly) invoke uninstall.exe
    # but unluckily this does not work.  So I decided to just stop a
    # (possibly) running neubot so that overwriting the directory works.
    # But, damn!, it's not clean at all to overwrite because we might
    # leave old files around.
    #
    execwait '"$INSTDIR\neubot.exe" stop'
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
    WriteRegStr HKLM                                                    \
      "Software\Microsoft\Windows\CurrentVersion\Uninstall\neubot"      \
      "DisplayName" "neubot 0.2.7"
    WriteRegStr HKLM                                                    \
      "Software\Microsoft\Windows\CurrentVersion\Uninstall\neubot"      \
      "UninstallString" "$INSTDIR\uninstall.exe"
sectionend
section "uninstall"
    #
    # We cannot use neubot-stop.exe because this program does not
    # wait for neubot.exe to terminate and so there is the risk to
    # issue the remove command while the file is already locked
    # and the remove will fail.
    #
    execwait '"$INSTDIR\neubot.exe" stop'
    rmdir /r "$INSTDIR"
    rmdir /r "$SMPROGRAMS\neubot"
    deleteregkey HKLM                                                   \
      "Software\Microsoft\Windows\CurrentVersion\Uninstall\neubot"
sectionend
