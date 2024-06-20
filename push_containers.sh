#!/bin/bash

ENV=$1
REGISTRY_REPO=registry.cern.ch/cms-dqmdc

if [ -z "$1" ]; then
    echo "Error: ENV variable not set. Please specify 'prod' or 'dev'."
    exit 1
fi

if [ "$ENV" = "prod" ]; then
    echo "Environment is production."
elif [ "$ENV" = "dev" ]; then
    echo "Environment is development."
else
    echo "Environment is neither production nor development."
    exit 1
fi

# Build
docker build -f ./backend/Dockerfile -t $REGISTRY_REPO/hdqm-backend-$ENV .
docker build -f ./frontend/Dockerfile -t $REGISTRY_REPO/hdqm-frontend-$ENV .

# login to registry and push containers
docker login https://registry.cern.ch
docker push $REGISTRY_REPO/hdqm-backend-$ENV
docker push $REGISTRY_REPO/hdqm-frontend-$ENV

