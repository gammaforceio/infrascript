#!/bin/bash -eu

VERSION=0.0.1

docker build \
  --tag "gammaforce/infra:${VERSION}" \
  --tag "gammaforce/infra:latest" \
    .
