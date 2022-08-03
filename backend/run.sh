#!/bin/bash

if [ "$1" == "-h" ] || [ "$1" == "--help" ];
then
    echo "Runs the app. Default port is 5000 but different port can be passed as a first argument."
    exit
fi

export PYTHONPATH=$(cd ../; pwd)/.python_packages/python3:$PYTHONPATH

if [ "$1" = "api" ]; then
  python3 api.py
fi

if [ "$1" = "extract" ]; then
  python3 dqm_extractor.py
fi
