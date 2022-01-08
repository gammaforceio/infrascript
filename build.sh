#!/bin/bash -eu

ORGANIZATION=gammaforceio
IMAGE=infra

# TODO: Have this read from a version file in the repository.
# TODO: Have that version file be stored the image.
VERSION=0.0.2

docker build \
  --tag "${ORGANIZATION}/${IMAGE}:${VERSION}" \
  --tag "${ORGANIZATION}/${IMAGE}:latest" \
    .
