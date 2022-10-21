#!/bin/sh

dir=`pwd`

if [ $USER != "cmsdqm" ]; then
    echo "Script must be run as user: cmsdqm"
    echo "Switch user: sudo su cmsdqm"
    exit -1
fi

src=$(date +%Y_%m_%d-%H_%M_%S)$(echo "_src")

git clone https://github.com/cms-dqm/CentralHDQM $src
cd $src
git checkout hdqm2

echo "export CLIENT_ID=FIXME" > backend/.env
echo "export CLIENT_SECRET=FIXME" >> backend/.env
echo "export AUDIENCE=FIXME" >> backend/.env
echo "export HDQM2_DB_PATH=FIXME" >> backend/.env

export RELEASE=/cvmfs/cms.cern.ch/slc7_amd64_gcc10/cms/cmssw/CMSSW_12_4_5
source /cvmfs/cms.cern.ch/cmsset_default.sh
cd $RELEASE
eval `scramv1 runtime -sh`
cd -

python3 -m pip install -r requirements.txt -t .python_packages/python3 --no-cache-dir

# Get back to main dir to switch the link
cd $dir

ln -s -f -n $src current

echo "New version started! Don't forget to restart: sudo systemctl restart hdqm2.service"

