#!/bin/bash -eu

ORGANIZATION=gammaforceio
IMAGE=infra
VERSION=0.0.2

docker login --username $ORGANIZATION
docker push "${ORGANIZATION}/${IMAGE}:${VERSION}"
docker push "${ORGANIZATION}/${IMAGE}:latest"
