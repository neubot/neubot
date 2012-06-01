#!/bin/sh -e

#
# Copyright (c) 2011 Alessio Palmero Aprosio <alessio@apnetwork.it>
#  Universita` degli Studi di Milano
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

#
# prerun.sh -- Make sure that Neubot can run.
#
# This scripts makes sure that Neubot can run, checking that
# all the needed users are installed, and so on.  It is invoked
# both by the installer and by the VERSIONDIR/start.sh script.
# The installer invokes it during postflight because it needs
# to run Neubot to setup the database with privacy permissions.
# VERSIONDIR/start.sh runs it unconditionally: the general
# idea is that this script is basically a noop if the special
# file VERSIONDIR/.skip-checks exists.  The presence of that
# file means that the script has already run for the current
# version of the software.
#

#
# The caller will use an absolute PATH so we can easily get
# the place where Neubot is installed using dirname.
#
VERSIONDIR=$(dirname $0)

logger -p daemon.info -t $0 "Neubot versiondir: $VERSIONDIR"

if [ -f $VERSIONDIR/.skip-checks ]; then
    logger -p daemon.info -t $0 'Nothing to do'
else

    # Application
    logger -p daemon.info -t $0 'Installing Application'
    rm -rf /Applications/Neubot.app /Applications/neubot.app
    ln -s $VERSIONDIR/Neubot.app /Applications

    # Command line usage
    rm -f /usr/local/bin/neubot
    install -d /usr/local/bin
    ln -s $VERSIONDIR/cmdline.sh /usr/local/bin/neubot

    # Manual page(s)
    rm -f /usr/local/share/man/man1/neubot.1
    install -d /usr/local/share/man/man1
    ln -s $VERSIONDIR/neubot.1 /usr/local/share/man/man1/neubot.1

    # Notifier
    logger -p daemon.info -t $0 'Installing notifier'
    install -m644 $VERSIONDIR/org.neubot.notifier.plist /Library/LaunchAgents

    # Comment-out because they are meaningful for logged users only
    #launchctl unload /Library/LaunchAgents/org.neubot.notifier.plist || true
    #launchctl load /Library/LaunchAgents/org.neubot.notifier.plist

    #
    # Group `_neubot`
    #

    MYGID=$(dscl . -list /Groups gid|awk '/^_neubot[ \t]/ {print $2}')

    if [ "$MYGID"x = ""x ]; then
        logger -p daemon.info -t $0 'Installing group _neubot'

        MINGID=1000
        MAXGID=65535

        while [ $MINGID -le $MAXGID ]; do
            if dscl . -list /Groups gid|grep -q "${MINGID}$"; then
                MINGID=$(($MINGID + 1))
            else
                MYGID=$MINGID
                break
            fi
        done

        if [ "$MYGID"x = ""x ]; then
            logger -p daemon.error -t $0 'Cannot install group _neubot'
            exit 1
        fi

        dscl . -create /Groups/_neubot gid $MYGID
    fi

    #
    # User `_neubot`
    #

    MYUID=$(dscl . -list /Users UniqueID|awk '/^_neubot[ \t]/ {print $2}')

    if [ "$MYUID"x = ""x ]; then
        logger -p daemon.info -t $0 'Installing user _neubot'

        MINUID=1000
        MAXUID=65535

        while [ $MINUID -le $MAXUID ]; do
            if dscl . -list /Users UniqueID|grep -q "${MINUID}$"; then
                MINUID=$(($MINUID + 1))
            else
                MYUID=$MINUID
                break
            fi
        done

        if [ "$MYUID"x = ""x ]; then
            logger -p daemon.error -t $0 'Cannot install user _neubot'
            exit 1
        fi

        dscl . -create /Users/_neubot UniqueID $MYUID
        dscl . -create /Users/_neubot PrimaryGroupID $MYGID
    fi

    # Update these records in any case
    dscl . -create /Users/_neubot UserShell /usr/bin/false
    dscl . -create /Users/_neubot RealName "Neubot privilege separation user"
    dscl . -create /Users/_neubot Password '*'

    #
    # Group `_neubot_update`
    #

    MYGID=$(dscl . -list /Groups gid|awk '/^_neubot_update[ \t]/ {print $2}')

    if [ "$MYGID"x = ""x ]; then
        logger -p daemon.info -t $0 'Installing group _neubot_update'

        MINGID=1000
        MAXGID=65535

        while [ $MINGID -le $MAXGID ]; do
            if dscl . -list /Groups gid|grep -q "${MINGID}$"; then
                MINGID=$(($MINGID + 1))
            else
                MYGID=$MINGID
                break
            fi
        done

        if [ "$MYGID"x = ""x ]; then
            logger -p daemon.error -t $0 'Cannot install group _neubot_update'
            exit 1
        fi

        dscl . -create /Groups/_neubot_update gid $MYGID
    fi

    #
    # User `_neubot_update`
    #

    MYUID=$(dscl . -list /Users UniqueID|awk '/^_neubot_update[ \t]/ {print $2}')

    if [ "$MYUID"x = ""x ]; then
        logger -p daemon.info -t $0 'Installing user _neubot_update'

        MINUID=1000
        MAXUID=65535

        while [ $MINUID -le $MAXUID ]; do
            if dscl . -list /Users UniqueID|grep -q "${MINUID}$"; then
                MINUID=$(($MINUID + 1))
            else
                MYUID=$MINUID
                break
            fi
        done

        if [ "$MYUID"x = ""x ]; then
            logger -p daemon.error -t $0 'Cannot install user _neubot_update'
            exit 1
        fi

        dscl . -create /Users/_neubot_update UniqueID $MYUID
        dscl . -create /Users/_neubot_update PrimaryGroupID $MYGID
    fi

    # Update these records in any case
    dscl . -create /Users/_neubot_update UserShell /usr/bin/false
    dscl . -create /Users/_neubot_update RealName "Neubot privilege separation user"
    dscl . -create /Users/_neubot_update Password '*'

    logger -p daemon.info -t $0 'Creating .skip-checks hint file'
    touch $VERSIONDIR/.skip-checks

    logger -p daemon.info -t $0 'Running sync(8)'
    sync
fi
