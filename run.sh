#!/bin/bash

# Bash script for running HDQM as 


if [ "$1" == "-h" ] || [ "$1" == "--help" ];
then
    echo "Runs HDQM's various services."
    echo ""
    echo "   run.sh api: Runs the API server. Default port is $PORT Select another one by passing it"
    echo "               as an argument after the command (e.g. run.sh api 6000)"
    echo ""
    echo "   run.sh extract: Runs the dqm_extractor.py script."
    exit
fi

source .env

# Activate venv
if [ ! -d venv ]; then
  echo "Virtual environment not found! Run update.sh first."
  exit
fi


if [ "$1" = "api" ]; then
  source venv/bin/activate
  
  PORT=5000
  if [ "$2" ]; then
    PORT=$2
  fi
  # No need to bind to 0.0.0.0, we have an nginx to take care of
  # exposing the port.
  gunicorn --workers=`nproc` 'backend.api:create_app()' --bind=127.0.0.1:$PORT
elif [ "$1" = "extract" ]; then
  source venv/bin/activate

  # Source ROOT activation script from CVMFS
  . /cvmfs/sft.cern.ch/lcg/app/releases/ROOT/6.24.08/x86_64-centos7-gcc48-opt/bin/thisroot.sh

  # Keep authenticating with kerberos to access EOS
  while true ; do
    kinit -kt /data/hdqm/.keytab cmsdqm
    /usr/bin/eosfusebind -g

    python3 backend/dqm_extractor.py
    sleep 3d
    #exit
  done
fi

