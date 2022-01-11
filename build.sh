#!/bin/bash -eu

# Go to the top of the repository
cd $(git rev-parse --show-toplevel)

ORGANIZATION=gammaforceio
IMAGE=infra

# TODO: Have that version file be stored the image.
VERSION=$(cat VERSION)

docker build \
  --tag "${ORGANIZATION}/${IMAGE}:${VERSION}" \
  --tag "${ORGANIZATION}/${IMAGE}:latest" \
    .
