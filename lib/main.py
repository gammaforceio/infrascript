#!/usr/bin/env python3
# vim: set ft=python:sw=4:ts=4

import os
import sys

# This location is set within the Dockerfile.
sys.path.insert(0, '/opt/infra/lib')

from infra import (
    load_definitions_file,
    parse_args,
    get_org_repo,
    cleanup_boilerplate,
    write_tf_backend_file,
    write_tfvars_file,
    run_terraform,
    save_outputs,
    write_awstf_file,
)

if __name__ == '__main__':
    # TODO: Ensure the AWS envvars are set

    GLOBALS, SECTIONS = load_definitions_file()

    args = parse_args(
        legal_sections=SECTIONS.keys(),
    )

    # TODO: Handle the None,None and the x,'' cases
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
            environment=args.environment,
            section=args.section,
        )

    section_values = SECTIONS.get(args.section, {}).get('inputs', {})
    tfvars_filename = write_tfvars_file(
        GLOBALS=GLOBALS,
        # These are the values that all sections must handle
        global_values={
            "environment": args.environment,

            # This will be used by the boilerplate aws.tf file
            "region": section_values.get('region', GLOBALS['region']),
        },
        section_values=section_values,
        org=org,
        repo=repo,
        environment=args.environment,
    )

    write_awstf_file()

    # TODO: Generate the boilerplate aws.tf file with the region variable

    # The output subcommand's STDOUT needs to be parseable as JSON.
    suppress_verbiage = False
    if args.subcmd == 'output':
        suppress_verbiage = True

    # Always run "terraform init". This is safe.
    run_terraform('init',
        reconfigure=args.reconfigure,
        tfvars_filename=tfvars_filename,
        suppress_verbiage=suppress_verbiage,
    )

    options = []

    suppress_input = True
    # Force -auto-approve otherwise terraform apply/destroy will error out.
    if args.subcmd == 'apply':
        options.append('-auto-approve')
    elif args.subcmd == 'destroy':
        options.append('-auto-approve')
    elif args.subcmd == 'output':
        # The output subcommand cannot handle the -var-file parameter.
        tfvars_filename = None
        suppress_input = False

        # Always display outputs in JSON
        options.append('-json')

    # Run the command we were asked to run.
    rv = run_terraform(args.subcmd,
        options=options,
        suppress_input=suppress_input,
        tfvars_filename=tfvars_filename,
        suppress_verbiage=suppress_verbiage,
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
            environment=args.environment,
            section=args.section,
        )

    cleanup_boilerplate()

    # Scripts should be clear when they succeed. A visual statement is helpful.
    if not suppress_verbiage:
        print("Ok", flush=True)
