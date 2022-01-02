#!/bin/bash -eu

GITROOT=$(git rev-parse --show-toplevel)
cd $GITROOT

# This presumes Git 2.14
PROJECT_NAME=$(git remote get-url origin | cut -d: -f2 | cut -d. -f1)

# Assumptions:
# * There is an infra/ directory at the root of the Git repository

cd infra
docker run --rm \
    --user "$(id -u):$(id -g)" \
    --volume "$(pwd):/terraform" \
    --workdir "/terraform" \
    --env AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
    --env AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
    --env AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN \
    --env SCM_PROJECT=$PROJECT_NAME \
        gammaforce\infra:latest

