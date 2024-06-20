#!/bin/bash

# Bash script for running HDQM as 

if [ "$1" == "-h" ] || [ "$1" == "--help" ];
then
    echo "Runs HDQM's various services."
    echo ""
    echo "   run.sh api: Runs the API server. Default PORT is 5000."
    echo ""
    echo "   run.sh extract: Runs the dqm_extractor.py script."
    exit
fi

if [ "$1" = "api" ]; then
  gunicorn --workers=`nproc` 'backend.api:create_app()' --bind=0.0.0.0:5000 --access-logfile=- --error-logfile=-
elif [ "$1" = "extract" ]; then
  python3 backend/dqm_extractor.py
fi

