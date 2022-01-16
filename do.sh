#!/bin/bash -eu

# Go to the top of the repository
cd $(git rev-parse --show-toplevel)

ORGANIZATION=gammaforceio
IMAGE=infra
TESTIMAGE=infratest

# TODO: Have that version file be stored the image.
VERSION=$(cat VERSION)

function build() {
  docker build \
    --tag "${ORGANIZATION}/${IMAGE}:${VERSION}" \
    --tag "${ORGANIZATION}/${IMAGE}:latest" \
      .
}

function build_test() {
  build

  docker build \
    -f Dockerfile.test \
    --tag "${ORGANIZATION}/${TESTIMAGE}:latest" \
      .
}

function push() {
  docker login --username $ORGANIZATION
  docker push "${ORGANIZATION}/${IMAGE}:${VERSION}"
  docker push "${ORGANIZATION}/${IMAGE}:latest"
}

fn_exists() { declare -F "$1" > /dev/null; }

function main() {
  cmd=$1;shift

  if ! fn_exists $cmd; then
    >&2 echo "$cmd is not defined"
    exit 1
  fi

  $cmd
}

main "$@"
