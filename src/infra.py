# vim: set ft=python:sw=4:ts=4

import argparse
import os
import sys

# Assumptions:
# * ???
def load_definitions_file():
    # TODO: Is this necessary within the Docker container?
    # We have to add the current directory to the module search path because
    # even though "." is appended, that's the directory the script was executed
    # from. We've already changed directory once, so make sure we have the
    # current directory there.
    sys.path.insert(0, os.getcwd())

    # This is a file we require to exist in order for this script to know what
    # to do. It must live in the infra/ directory.
    #
    # TODO:
    # * Make sure
    #   * this file exists
    #   * compiles properly
    # * Allow this filename to be set
    from definitions import GLOBALS, SECTIONS

    have_error = False
    if 'type' not in GLOBALS:
        print("type not set in GLOBALS", file=sys.stderr)
        have_error = True
    elif GLOBALS['type'].lower() not in ['aws', 'gcp']:
        print(f"{GLOBALS['type']} not in ('aws', 'gcp')", file=sys.stderr)
        have_error = True
    elif GLOBALS['type'].lower() == 'aws':
        if 'backend' not in GLOBALS:
            print("backend not set in GLOBALS", file=sys.stderr)
            have_error = True
        else:
            if 'bucket_name' not in GLOBALS['backend']:
                print("bucket_name not set in GLOBALS['backend']", file=sys.stderr)
                have_error = True
            if 'dynamodb_table' not in GLOBALS['backend']:
                print("dynamodb_table not set in GLOBALS['backend']", file=sys.stderr)
                have_error = True
    elif GLOBALS['type'].lower() == 'gcp':
        if 'backend' not in GLOBALS:
            print("backend not set in GLOBALS", file=sys.stderr)
            have_error = True
        else:
            if 'bucket_name' not in GLOBALS['backend']:
                print("bucket_name not set in GLOBALS['backend']", file=sys.stderr)
                have_error = True

    # TODO Verify that:
    # * GLOBALS['region'] is set and has a correct value for 'type'
    # * each SECTION in SECTIONS has:
    #   * inputs doesn't exist or is a dict whose values are correct
    #   * (subdir, key) is a subdirectory

    if have_error:
        sys.exit(1)

    return GLOBALS, SECTIONS

# TODO: Handle the None,None and the x,'' cases
def get_org_repo():
    project = os.getenv('SCM_PROJECT')
    if project is None:
        return None, None
    vals = project.split('/')
    vals.extend(['', ''])
    return vals[0:2]
