#!/bin/bash -eu

# Go to the top of the repository
cd $(git rev-parse --show-toplevel)

ORGANIZATION=gammaforceio
IMAGE=infra
TESTIMAGE=infratest

# TODO: Have that version file be stored the image.
VERSION=$(cat VERSION)

VERSIONED_IMAGE="${ORGANIZATION}/${IMAGE}:${VERSION}"
LATEST_IMAGE="${ORGANIZATION}/${IMAGE}:latest"
FULL_TEST_IMAGE="${ORGANIZATION}/${TESTIMAGE}:latest"

function build() {
  docker build \
    -q \
    --tag "${VERSIONED_IMAGE}" \
    --tag "${LATEST_IMAGE}" \
      .
}

function build_test() {
  build

  docker build \
    -q \
    -f Dockerfile.test \
    --tag "${FULL_TEST_IMAGE}" \
      .
}

function run_tests() {
  build_test

  mkdir -p htmlcov

  docker run \
    --user "$(id -u):$(id -g)" \
    --rm \
    --volume "$(pwd)/htmlcov:/scripts/htmlcov" \
      "${FULL_TEST_IMAGE}" "$@"
}

function login_to_image() {
  build

  docker run \
    --user "$(id -u):$(id -g)" \
    --rm -it \
    --entrypoint "/bin/sh" \
      "${LATEST_IMAGE}"
}

function login_to_testimage() {
  build_test

  mkdir -p htmlcov

  docker run \
    --user "$(id -u):$(id -g)" \
    --rm -it \
    --volume "$(pwd)/htmlcov:/scripts/htmlcov" \
    --entrypoint "/bin/sh" \
      "${FULL_TEST_IMAGE}"
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

  $cmd "$@"
}

main "$@"
