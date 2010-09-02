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

CURRENT=`grep ^VERSION Makefile | sed 's/^VERSION[\t ]*=[\t ]*//'`
CURRENT_MAJOR=`echo $CURRENT | cut -d. -f1`
CURRENT_MINOR=`echo $CURRENT | cut -d. -f2`
CURRENT_PATCH=`echo $CURRENT | cut -d. -f3`

#
# Compute new version number
#

if [ $# -eq 1 ]; then
    NEW=$1
    NEW_MAJOR=`echo $NEW | cut -d. -f1`
    NEW_MINOR=`echo $NEW | cut -d. -f1`
    NEW_PATCH=`echo $NEW | cut -d. -f1`
elif [ $# -eq 0 ]; then
    if [ "$CURRENT_MINOR" -eq "9" ]; then
        NEW_MAJOR=$(($CURRENT_MAJOR+1))
        NEW_MINOR=0
        NEW_PATCH=0
    elif [ "$CURRENT_PATCH" -eq "9" ]; then
        NEW_MAJOR=$CURRENT_MAJOR
        NEW_MINOR=$(($CURRENT_MINOR+1))
        NEW_PATCH=0
    else
        NEW_MAJOR=$CURRENT_MAJOR
        NEW_MINOR=$CURRENT_MINOR
        NEW_PATCH=$(($CURRENT_PATCH+1))
    fi
    NEW="$NEW_MAJOR.$NEW_MINOR.$NEW_PATCH"
else
    printf "Usage: %s [version]\n", $0 1>&2
    exit 1
fi

#
# Update ChangeLog.
# We assume `sed -i' is valid.
# XXX If there are not changes between the current HEAD and the
# previous release there is a bug and we zap the date from the
# ChangeLog.
#

DATE=`date +%F`
printf "Neubot $NEW [$DATE]\n" > ChangeLog.in
git shortlog $CURRENT..HEAD | sed -n '2,$p' >> ChangeLog.in
sed -i '$d' ChangeLog.in
sed -i '2,$s/^\ */	* /' ChangeLog.in
printf "\t* Release neubot/$NEW\n\n" >> ChangeLog.in
cat ChangeLog >> ChangeLog.in
mv ChangeLog.in ChangeLog

#
# Update version number.
# Make sure we don't touch the ChangeLog.
# We assume `sed -i' is valid.
#

PATTERN="$CURRENT_MAJOR\\.$CURRENT_MINOR\\.$CURRENT_PATCH"
FILES=`grep -Rn $PATTERN *|grep -v ^ChangeLog|awk -F: '{print $1}'|sort -u`
for FILE in $FILES; do
    sed -i s/$PATTERN/$NEW/g $FILE
done

#
# Commit
#

git commit -a -m "Release neubot/$NEW"
git tag $NEW
