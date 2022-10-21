#!/bin/bash

if [ "$1" == "-h" ] || [ "$1" == "--help" ];
then
    echo "Runs the app. Default port is 5000 but different port can be passed as a first argument."
    exit
fi

source .env

if [ "$1" = "api" ]; then
  export PYTHONPATH=$(cd ../; pwd)/.python_packages/python3:$PYTHONPATH
  python3 api.py
fi

if [ "$1" = "extract" ]; then
  export RELEASE=/cvmfs/cms.cern.ch/slc7_amd64_gcc10/cms/cmssw/CMSSW_12_4_5
  source /cvmfs/cms.cern.ch/cmsset_default.sh
  cd $RELEASE
  eval `scramv1 runtime -sh`
  cd -
  export PYTHONPATH=$(cd ../; pwd)/.python_packages/python3:$PYTHONPATH

  while true ; do
    kinit -kt /data/hdqm/.keytab cmsdqm
    /usr/bin/eosfusebind -g

    db_name="$(mktemp --dry-run hdqm_XXXXXXXX.db)"
    echo $db_name
    # cp hdqm_v3.db $db_name
    python3 dqm_extractor.py
    sleep 3d
    #exit
  done
fi

