#!/bin/bash -eux

# TODO:
# * Throw an error if we're not in a Git repository

# By doing this, we allow this script to be invoked anywhere within the Git
# repository. This allows it to be treated as a command and not as a script.
GITROOT=$(git rev-parse --show-toplevel)
cd $GITROOT

# This presumes Git 2.14
PROJECT_NAME=$(git remote get-url origin | cut -d: -f2 | cut -d. -f1)

# TODO: Validate the following assumptions:
# * There is an infra/ directory at the root of the Git repository
# * The definitions.py file exists in that directory
# * The Terraform directories are children of that directory

cd infra
exec docker run --rm \
    --user "$(id -u):$(id -g)" \
    --volume "$(pwd):/terraform" \
    --workdir "/terraform" \
    --env AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
    --env AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
    --env SCM_PROJECT=$PROJECT_NAME \
        gammaforce/infra:latest $@
