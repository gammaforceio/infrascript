#!/bin/bash -eu

# Go to the top of the repository
cd $(git rev-parse --show-toplevel)

ORGANIZATION=gammaforceio
IMAGE=infra
VERSION=$(cat VERSION)

docker login --username $ORGANIZATION
docker push "${ORGANIZATION}/${IMAGE}:${VERSION}"
docker push "${ORGANIZATION}/${IMAGE}:latest"
