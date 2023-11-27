#!/bin/bash

set -eu

# This Bash script is provided as an example of how to properly invoke the
# infrascript image.
#
# These are the assumptions that must be met:
# * The --user line must exist so that any files written can be cleaned up
# * The working directory must be the directory with the definitions.py file
# * The --volume/--workdir pairing is important so that everything mounts into
#   the container properly
# * The PROJECT_NAME setting is important for the LookupOutput helper to
#   reference outputs from other repositories.
#   * This value must be formatted as "org/repo"
# * The AWS envvars are necessary if you're running with the AWS backend
# * TODO: The GCP envvars ...

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

# This can be whatever you want - it's your directory structure.
cd infra
exec docker run --rm \
    --user "$(id -u):$(id -g)" \
    --volume "$(pwd):/terraform" \
    --workdir "/terraform" \
    --env AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
    --env AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
    --env SCM_PROJECT=$PROJECT_NAME \
        gammaforceio/infra:latest $@
