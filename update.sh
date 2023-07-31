#!/bin/sh

dir=`pwd`

if [ $USER != "cmsdqm" ]; then
    echo "Script must be run as user: cmsdqm"
    echo "Switch user: sudo su cmsdqm"
    exit 1
fi

# Creates a new directory to clone the source files into.
src=$(date +%Y_%m_%d-%H_%M_%S)$(echo "_src")

git clone https://github.com/cms-dqm/CentralHDQM $src
cd $src
git checkout master

# Copy the .env file: It's expected to be found in /data/hdqm.
if [! -f ../.env]; then
    echo "A file named .env is expected to be in the same directory with update.sh; Create it and rerun the script"
    exit 1
fi
cp ../.env ./backend/


# Create a venv, activate it, install requirements.
PYTHON=`(which python3)`
$PYTHON -m venv venv
source venv/bin/activate
$PYTHON -m pip install -r requirements.txt -U --no-cache-dir

# Add ROOT to PATH (includes PyROOT)
. /cvmfs/sft.cern.ch/lcg/app/releases/ROOT/6.24.08/x86_64-centos7-gcc48-opt/bin/thisroot.sh

# Get back to main dir to switch the link
cd $dir

# Softlink latest source files to a link named "current"
ln -s -f -n $src current

echo "New version started! Don't forget to restart: sudo systemctl restart hdqm.service"

