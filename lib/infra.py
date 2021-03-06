#!/usr/bin/env python3
# vim: set ft=python:sw=4:ts=4

import argparse
import boto3
from collections.abc import Mapping, Sequence, Set
from functools import reduce
import json
import os
import subprocess
import sys
from tempfile import NamedTemporaryFile

from lookup_output import LookupOutput, get_outputs_key
from per_environment import EnvironmentNotFoundError, PerEnvironment

# TODO:
# * Create a method that writes to a tempfile and use it within
#   write_tf_backend_file() and write_tfvars_file()

# Assumptions:
# * ???
def load_definitions_file():
    # We have to add the current directory to the module search path because
    # even though "." is appended, that's the directory the script was executed
    # from. We've already changed directory once, so make sure we have the
    # current directory there.
    sys.path.insert(0, os.getcwd())

    # This is a file we require to exist in order for this script to know what
    # to do. It must live in the infra/ directory.
    #
    # TODO: Make sure this file exists, compiles properly, and provides these
    # data structures.
    from definitions import GLOBALS, SECTIONS

    return GLOBALS, SECTIONS

def parse_args(legal_sections):
    parser = argparse.ArgumentParser(description='Run infrastructure stuff')
    parser.add_argument('subcmd', help='Terraform subcommand', choices=['plan', 'apply', 'destroy', 'output'])
    parser.add_argument('section', help="what are we subcmd'ing?", choices=legal_sections)
    parser.add_argument('--no-backend', action='store_true', help='skip TF backend')
    parser.add_argument('--reconfigure', action='store_true', help='Reconfigure state (used only when creating the TF backend')
    parser.add_argument('--environment', default='prod', help='Environment (default: prod)')

    return parser.parse_args()

def cleanup_boilerplate():
    # TODO: Make this into a Pythonic command
    os.system('rm -f boilerplate-*')
    os.system('rm -rf .terraform')

def write_awstf_file():
    tempfile = NamedTemporaryFile(dir='.', prefix='boilerplate-', suffix='.tf', delete=False)
    with open(tempfile.name, 'w') as fh:
        # The doubled-braces are to handle how f-strings deal with them.
        # Otherwise, this will be a syntax error.
        fh.write(f"""
variable "region" {{
  type = string
  nullable = false
}}

provider aws {{
  region = var.region
}}

data "aws_caller_identity" "current" {{}}
        """)
        fh.flush()

    return os.path.basename(tempfile.name)

def write_tf_backend_file(
    bucket, region, dynamodb_table,
    org, repo, environment, section,
):
    key = f"terraform/state/{org}/{repo}/{environment}/{section}.tfstate"

    tempfile = NamedTemporaryFile(dir='.', prefix='boilerplate-', suffix='.tf', delete=False)
    with open(tempfile.name, 'w') as fh:
        # The doubled-braces are to handle how f-strings deal with them.
        # Otherwise, this will be a syntax error.
        fh.write(f"""
terraform {{
    backend "s3" {{
        bucket = "{bucket}"
        key = "{key}"
        region = "{region}"
        dynamodb_table = "{dynamodb_table}"
    }}
}}
        """)
        fh.flush()

    return os.path.basename(tempfile.name)

def _resolve_section_values(GLOBALS, section_values, org, repo, environment):
    # The full walking code is at https://code.activestate.com/recipes/577982/.
    # This is adapted to walk over and modify section_values.
    string_types = (str, bytes)
    iteritems = lambda mapping: getattr(mapping, 'iteritems', mapping.items)()
    def __walk(obj, path=(), memo=None):
        if memo is None:
            memo = set()
        iterator = None
        if isinstance(obj, Mapping):
            iterator = iteritems
        elif isinstance(obj, (Sequence, Set)) and not isinstance(obj, string_types):
            iterator = enumerate
        if iterator:
            if id(obj) not in memo:
                memo.add(id(obj))
                for key, value in iterator(obj):
                    for result in __walk(value, path+(key,), memo):
                        yield result
                memo.remove(id(obj))
        else:
            yield path, obj

    # This is unused, but provided for completeness
    # def __get(obj, keys):
    #     return reduce(lambda c,k: c.get(k, {}), keys, obj)
    def __set(obj, keys, value):
        keys = list(keys)
        k = keys.pop(0)
        while len(keys) > 0:
            obj = obj[k]
            k = keys.pop(0)
        obj[k] = value


    # Resolve values in this order:
    #   1. PerEnvironment
    #   2. LookupOutput
    # This allows PerEnvironment objects to reference LookupOutput objects.
    for path, value in __walk(section_values):
        if isinstance(value, PerEnvironment):
            value = value.resolve(
                environment=environment,
            )

        if isinstance(value, LookupOutput):
            value = value.resolve(
                bucket_name=GLOBALS['backend']['bucket_name'],
                org=org,
                repo=repo,
                environment=environment,
            )

        __set(section_values, path, value)

    return section_values

def write_tfvars_file(GLOBALS, global_values, section_values, org, repo, environment):
    # This modifies section_values's keys and values, so it does not need to be
    # returned. The actual section_values dict object is unchanged, so Python's
    # pass-by-value semantics are preserved.
    _resolve_section_values(
        GLOBALS=GLOBALS,
        section_values=section_values,
        org=org,
        repo=repo,
        environment=environment,
    )

    output = global_values.copy()
    output.update(section_values)

    tempfile = NamedTemporaryFile(dir='.', prefix='boilerplate-', suffix='.tfvars.json', delete=False)
    with open(tempfile.name, 'w') as fh:
        json.dump(output, fh)
        fh.flush()

    return os.path.basename(tempfile.name)

# q.v. https://learn.hashicorp.com/tutorials/terraform/automate-terraform
def run_terraform(subcmd, tfvars_filename=None, suppress_input=True, reconfigure=False, options=[], stream_output=True, suppress_verbiage=False):
    cmd = ['terraform']

    cmd.append(subcmd)

    if reconfigure:
        cmd.append('-reconfigure')
        cmd.append('-force-copy')
    elif suppress_input:
        # We're running in automation, so always suppress -input
        # TODO: Figure out why this broke using --no-backend / --reconfigure
        cmd.append('-input=false')

    cmd = cmd + options

    if tfvars_filename:
        cmd.append(f'-var-file={tfvars_filename}')

    # TODO: Put this behind an "if debug"
    #print(f"{' '.join(cmd)}", flush=True)

    # These lines are here in case you want to pause right before execution.
    #import time
    #time.sleep(1000)

    if stream_output and not suppress_verbiage:
        print(f"Running {subcmd}", flush=True)

    return run_command(cmd, stream=stream_output and subcmd != 'init')

def save_outputs(bucket, org, repo, environment, section):
    outputs = run_terraform("output",
        options=['-json'],
        suppress_input=False,
        stream_output=False,
    )

    key = get_outputs_key(org, repo, environment, section)
    s3 = boto3.resource('s3')
    s3.Object(bucket, key).put(Body=outputs)

    print(f"Outputs saved to s3://{bucket}/{key}", flush=True)

# TODO: This needs to handle and propagate failure
def run_command(cmd, stream=False):
    # We want to stream the results back to the user. We want to return
    # success or failure to the invoker.
    if stream:
        return subprocess.run(
            cmd,
            capture_output=False,
        )
    # We're not streaming, so capture and return the output to the invoker.
    else:
        return subprocess.Popen(
            cmd, stdout=subprocess.PIPE,
        ).communicate()[0].rstrip().decode('utf-8')

def get_org_repo():
    project = os.getenv('SCM_PROJECT')
    if project is None:
        return None, None
    vals = project.split('/')
    vals.extend(['', ''])
    return vals[0:2]
