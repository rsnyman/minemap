#!/bin/sh
# symlink minemap into your path so you can run it in the terminal from any directory.
# It will link into your ~/bin, and failing that /usr/bin is used (which will use sudo).
USRBIN="$HOME/bin"
SYSBIN="/usr/bin"
SYMLINK=`which minemap`
if [ -z $SYMLINK ]; then
    if [ -d $USRBIN ]; then
        echo "Symlinking minemap into $USRBIN"
        ln -s $PWD/minemap.py $USRBIN/minemap
    elif [ -d $SYSBIN ]; then
        echo "Symlinking minemap into $SYSBIN. sudo is required."
        sudo ln -s $PWD/minemap.py $SYSBIN/minemap
    else
        echo "Neither $USRBIN or $SYSBIN exist :("
    fi
else
    echo "minemap is already linked as $SYMLINK."
    echo "If this is wrong then remove it and run this again."
fi
