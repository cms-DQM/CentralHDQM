#!/bin/sh

dir=`pwd`

if [ $USER != "cmsdqm" ]; then
    echo "Script must be run as user: cmsdqm"
    echo "Switch user: sudo su cmsdqm"
    exit -1
fi

# Creates a new directory to clone the source files into.
src=$(date +%Y_%m_%d-%H_%M_%S)$(echo "_src")

git clone https://github.com/cms-dqm/CentralHDQM $src
cd $src
git checkout master

# Copy the .env file
cp ../.env ./backend/

# TODO: Why is CMSSW needed?
export RELEASE=/cvmfs/cms.cern.ch/slc7_amd64_gcc10/cms/cmssw/CMSSW_12_4_5
source /cvmfs/cms.cern.ch/cmsset_default.sh
cd $RELEASE
eval `scramv1 runtime -sh`
cd -  # Go back to $src

# Create a venv, activate it, install requirements.
PYTHON=`(which python3)`
$PYTHON -m venv venv
source venv/bin/activate
$PYTHON -m pip install -r requirements.txt -U --no-cache-dir

# Get back to main dir to switch the link
cd $dir

# Softlink latest source files to a link named "current"
ln -s -f -n $src current

echo "New version started! Don't forget to restart: sudo systemctl restart hdqm2.service"

