#!/usr/bin/env python3
# vim: set ft=python:sw=4:ts=4

TF_VERSION = "1.1.1"

import argparse
import boto3
import json
import os
import subprocess
import sys
from tempfile import NamedTemporaryFile

sys.path.insert(0, '/scripts')
from lookup_output import LookupOutput, get_outputs_key

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

    return parser.parse_args()

def cleanup_boilerplate():
    # TODO: Make this into a Pythonic command
    os.system('rm -f boilerplate-*')
    os.system('rm -rf .terraform')

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

def write_tfvars_file(GLOBALS, global_values, section_values, org, repo, environment):
    # Currently, this only looks down a single level. It will need to be expand
    # to do a full walk if we need resolution further down.
    # q.v. https://code.activestate.com/recipes/577982/
    for key in section_values.keys():
        if isinstance(section_values[key], LookupOutput):
            section_values[key] = section_values[key].resolve(
                bucket_name=GLOBALS['backend']['bucket_name'],
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
def run_terraform(subcmd, tfvars_filename=None, reconfigure=False, options=[], stream_output=True):
    cmd = ['terraform']

    cmd.append(subcmd)

    # We're running in automation, so always suppress -input
    # TODO: Figure out why this broke when using --no-backend / --reconfigure
    #cmd.append('-input=false')

    if reconfigure:
        cmd.append('-reconfigure')
        cmd.append('-force-copy')

    cmd = cmd + options

    if tfvars_filename:
        cmd.append(f'-var-file={tfvars_filename}')

    # TODO: Put this behind an "if debug"
    #print(f"{' '.join(cmd)}", flush=True)

    # These lines are here in case you want to pause right before execution.
    #import time
    #time.sleep(1000)

    if stream_output:
        print(f"Running {subcmd}", flush=True)

    return run_command(cmd, stream=stream_output and subcmd != 'init')

def save_outputs(bucket, org, repo, environment, section):
    outputs = run_terraform("output",
        options=['-json'],
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

################################################################################
# Below here is the main code of this script. Everything above are the functions
# this script uses.
#
# We'll refactor this to be a proper CLI+lib for testability later.
################################################################################

if __name__ == '__main__':
    # TODO: Ensure the AWS envvars are set

    GLOBALS, SECTIONS = load_definitions_file()

    args = parse_args(
        legal_sections=SECTIONS.keys(),
    )

    # TODO: Make this an input parameter.
    environment = 'prod'

    org, repo = get_org_repo()

    # Set ourselves in the right directory. This simplifies the rest of the code
    # The directory is either specified in the SECTIONS definition or defaults
    # to the section name.
    os.chdir(SECTIONS[args.section].get('subdir', args.section))

    cleanup_boilerplate()

    # There are a very few cases where we don't want to write a TF backend file.
    # Specifically, when we're creating the TF backend in the first place.
    if not args.no_backend:
        write_tf_backend_file(
            region=GLOBALS['region'],
            bucket=GLOBALS['backend']['bucket_name'],
            dynamodb_table=GLOBALS['backend']['dynamodb_table'],
            org=org,
            repo=repo,
            environment=environment,
            section=args.section,
        )

    tfvars_filename = write_tfvars_file(
        GLOBALS=GLOBALS,
        # These are the values that all sections must handle
        global_values={
            "environment": environment,

            # This will be used by the boilerplate aws.tf file
            "region": GLOBALS['region'],
        },
        section_values=SECTIONS.get(args.section, {}).get('inputs', {}),
        org=org,
        repo=repo,
        environment=environment,
    )

    # TODO: Generate the boilerplate aws.tf file with the region variable

    # Always run "terraform init". This is safe.
    run_terraform('init',
        reconfigure=args.reconfigure,
        tfvars_filename=tfvars_filename,
    )

    options = []

    # Force -auto-approve otherwise terraform apply will error out.
    if args.subcmd == 'apply':
        options.append('-auto-approve')

    if args.subcmd == 'output':
        # The output subcommand cannot handle the -var-file parameter.
        tfvars_filename = None

        # Always display outputs in JSON
        options.append('-json')

    # Run the command we were asked to run.
    rv = run_terraform(args.subcmd,
        options=options,
        tfvars_filename=tfvars_filename,
    )
    # TODO: Do something here with rv - it's a CompletedProcess object
    # q.v. https://docs.python.org/3/library/subprocess.html#subprocess.CompletedProcess

    # TODO: Add a remove_outputs() to be called when destroying
    # TODO: Add a read_outputs() to be used when reading
    if args.subcmd == 'apply':
        save_outputs(
            bucket=GLOBALS['backend']['bucket_name'],
            org=org,
            repo=repo,
            environment=environment,
            section=args.section,
        )

    cleanup_boilerplate()

    # Scripts should be clear when they succeed. A visual statement is helpful.
    print("Ok", flush=True)
