#!/bin/bash

REGISTRY_REPO=registry.cern.ch/cms-dqmdc

# Build
docker build -f ./backend/Dockerfile -t $REGISTRY_REPO/hdqm-backend .
docker build -f ./frontend/Dockerfile -t $REGISTRY_REPO/hdqm-frontend .

# login to registry and push containers
docker login https://registry.cern.ch
docker push $REGISTRY_REPO/hdqm-backend
docker push $REGISTRY_REPO/hdqm-frontend

