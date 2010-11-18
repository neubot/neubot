#!/bin/sh

# release.sh
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
# Get current version number
#

# Note: the two char classes below contain a space and a tab
CURRENT=`grep ^VERSION Makefile | sed 's/^VERSION[ 	]*=[ 	]*//'`
CURRENT_MAJOR=`echo $CURRENT | cut -d. -f1`
CURRENT_MINOR=`echo $CURRENT | cut -d. -f2`
CURRENT_PATCH=`echo $CURRENT | cut -d. -f3`

#
# Compute new version number
#

if [ $# -eq 1 ]; then
    NEW=$1
elif [ $# -eq 0 ]; then
    NEW_MAJOR=$CURRENT_MAJOR
    NEW_MINOR=$CURRENT_MINOR
    NEW_PATCH=$(($CURRENT_PATCH+1))
    NEW="$NEW_MAJOR.$NEW_MINOR.$NEW_PATCH"
else
    printf "Usage: %s [version]\n", $0 1>&2
    exit 1
fi

#
# Update ChangeLog.
#

DATE=`date +%F`
printf "Neubot $NEW [$DATE]\n" > ChangeLog.in
git log --oneline --reverse --format="%x09* %s" $CURRENT..HEAD >> ChangeLog.in
printf "\t* Release neubot/$NEW\n\n" >> ChangeLog.in
cat ChangeLog >> ChangeLog.in
mv ChangeLog.in ChangeLog

#
# Update version number.
# Make sure we don't touch the ChangeLog.
# We don't assume `sed -i' is valid.
#

PATTERN="$CURRENT_MAJOR\\.$CURRENT_MINOR\\.$CURRENT_PATCH"
FILES=`grep -Rn $PATTERN *|grep -v ^ChangeLog|awk -F: '{print $1}'|sort -u`
for FILE in $FILES; do
    sed s/$PATTERN/$NEW/g $FILE > $FILE.new &&
     cat $FILE.new > $FILE && rm $FILE.new
done

#
# Commit
#

git commit -a -m "Release neubot/$NEW"
git tag $NEW
