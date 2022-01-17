#!/bin/sh

# This script exists to run Python coverage within the infratest Docker container.
# We cannot run this as an ENTRYPOINT because we want the ability to pass in the
# CLI options provided to the docker run command into the first command, then run a
# second command after.

# Write the coverage database to htmlcov which is a directory the running user can
# write to.
export COVERAGE_FILE="/scripts/htmlcov/.coverage"

coverage run -m pytest "$@"
coverage html

echo "You can now open htmlcov/index.html for coverage statistics"
