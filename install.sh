#!/bin/bash

if [[ "$*" == *"--help"* || "$*" == *"-h"* ]]; then
    echo "--system    / -s: (un)install untis-py system-wide (by default, the install will limit itself to the users home directory)"
    echo "--uninstall / -u: Uninstall untis-py. --system is needed to remove a system-wide installation."
    echo "--help      / -h: Display this text, then exit."
    exit 0
fi

if [[ "$*" == *"--system"* || "$*" == *"-s"* ]]; then
    if [ $(id -u) -ne 0 ]; then
        echo "Cannot (un)install system-wide without root permission!" 
        echo "Rerun this script with root permissions or perform a local (un)install."
        exit 1
    fi
    E_DIR="/opt/untis-py"
    D_PATH="/usr/share/applications"
    B_DIR="/usr/bin"
    U_MSG="Check if this installation is local (inside \$HOME)"
else
    if [ $(id -u) -e 0 ]; then
        echo "Refusing to (un)install locally with root permission!"
        echo "Rerun this script without root permissions or perform a system-wide (un)install."
        exit 1
    fi
    E_DIR="$HOME/.local/share/untis-py" # not exactly standardized, there does not appear to be a proper place for multi-file programs in $HOME
    D_PATH="$HOME/.local/share/applications"
    B_DIR="$HOME/.local/bin"
    U_MSG="Check if this installation is system-wide."
fi

if [[ "$*" == *"--uninstall"* || "$*" == *"-u"* ]]; then
    EXITCODE=0
    if [ ! -f "$D_PATH/untis.desktop" ]; then
        echo "Did not find untis.desktop file. $U_MSG"
        exit 1
    else
        rm "$D_PATH/untis.desktop"
        if [ -f "$D_PATH/untis.desktop" ]; then
            echo "Found untis.desktop, but failed to remove it. Check permissions (use sudo?)"
            exit 1
        fi
    fi
    if [ ! -f "$E_DIR/main.py" ]; then
        echo "Did not find content of install directory. $U_MSG"
        exit 1
    else
        rm -rf "$E_DIR"
        if [ -f "$E_DIR/main.py" ]; then
            echo "Found install directory, but failed to remove it. Check permissions (use sudo?)"
            exit 1
        fi
    fi
    if [ ! -f "$B_DIR/untis" ]; then
        echo "Did not find 'untis' command. $U_MSG"
        exit 1
    else
        rm "$B_DIR/untis"
        if [ -f "$B_DIR/untis" ]; then
            echo "Found 'untis' command, but failed to remove it. Check permissions (use sudo?)"
            exit 1
        fi
    fi
    echo "Success, untis-py uninstalled!"
    exit 0
fi

echo "[Desktop Entry]
Type=Application
Version=1.0
Name=Untis
Comment=Untis Client for Linux
Path=$E_DIR
Exec=python3 ./main.py
Icon=$E_DIR/icon.ico
Terminal=false
Categories=Education" > "$D_PATH/untis.desktop"
if [ ! -f "$D_PATH/untis.desktop" ]; then
    echo "Failed to create untis.desktop in directory $D_PATH"
    exit 1
fi
mkdir -p $E_DIR
cp -u ./* $E_DIR 2>/dev/null # "cp: -r not specified; omitting directory './__pycache__'" is fine, suppress that
if [ ! -f "$E_DIR/main.py" ]; then
    rm "$D_PATH/untis.desktop"
    echo "Failed to copy files to $E_DIR!"
    if [ -f "$D_PATH/untis.desktop" ]; then
        echo "Failed to undo previous change of creating $D_PATH/untis.desktop, installation incomplete."
        echo "Rerunning the installation with sufficient permissions or manually removing $D_PATH/untis.desktop will fix this."
    fi
    echo "Ensure install.sh is started with sufficient permissions (maybe use 'sudo ./install.sh')"
    exit 1
fi

# register untis command
echo "#!/bin/sh
PREV_DIR=$(pwd)
cd $E_DIR
python3 ./main.py
cd $PREV_DIR" > "$B_DIR/untis"
chmod +x "$B_DIR/untis"

echo "Installation completed without errors!"
