# vim: set ft=python:sw=4:ts=4

import fire
import os
import sys

# This location is set within the Dockerfile.
sys.path.insert(0, '/opt/gammaforce')

from infrascript.infra import (
    get_org_repo,
    load_definitions_file,
)
from infrascript.manager import get_manager

# TODO:
# * Need to add subcommands to:
#   * Check if it exists
#   * Apply/Update
#   * Destroy
#
# TEST THE APPLY CODE IN GFBF
#
def bootstrap(subcmd):
    if subcmd not in ['plan', 'apply', 'destroy']:
        print(f"{subcmd} not in ('plan', 'apply', 'destroy')", file=sys.stderr)
        sys.exit(1)

    section = '__bootstrap__'
    environment = 'prod'

    GLOBALS, SECTIONS = load_definitions_file()
    iaas = GLOBALS['type'].lower()

    # Delegate this to the manager object?
    SECTIONS = {
        section: {
            'inputs': {
                'bucket_name': GLOBALS['backend']['bucket_name'],
                'dynamodb_table': GLOBALS['backend']['dynamodb_table'],
            },
            'subdir': f"/opt/gammaforce/resources/bootstrap/{iaas}",
        },
    }

    # TODO:
    # * Need to distinguish between plan without anything build and plan with
    #   stuff built (with_backend=False vs. True)
    # * Need to handle failures in the first apply command so that it's not
    #   propagated to the second
    # * Need to distinguish between apply without anything built (first apply)
    #   and apply to update (with stuff built)
    if subcmd == 'plan':
        tf_cmd('plan', section, environment, GLOBALS, SECTIONS)
    elif subcmd == 'apply':
        tf_cmd('apply', section, environment, GLOBALS, SECTIONS, with_backend=False)
        tf_cmd('apply', section, environment, GLOBALS, SECTIONS, reconfigure=True)
    elif subcmd == 'destroy':
        tf_cmd('destroy', section, environment, GLOBALS, SECTIONS)

    return

def plan(section, environment='prod'):
    GLOBALS, SECTIONS = load_definitions_file()
    return tf_cmd('plan', section, environment, GLOBALS, SECTIONS)
def apply(section, environment='prod'):
    GLOBALS, SECTIONS = load_definitions_file()
    return tf_cmd('apply', section, environment, GLOBALS, SECTIONS)
def destroy(section, environment='prod'):
    GLOBALS, SECTIONS = load_definitions_file()
    return tf_cmd('destroy', section, environment, GLOBALS, SECTIONS)
def output(section, environment='prod'):
    GLOBALS, SECTIONS = load_definitions_file()
    return tf_cmd('output', section, environment, GLOBALS, SECTIONS)

def tf_cmd(
    subcmd,
    section,
    environment,
    GLOBALS,
    SECTIONS,
    with_backend=True,
    reconfigure=False,
):
    # TODO: Ensure the IaaS (AWS/GCP) envvars are set

    # TODO: Verify the section parameter

    # Set ourselves in the right directory. This simplifies the rest of the code
    # The directory is either specified in the SECTIONS definition or defaults
    # to the section name.
    os.chdir(SECTIONS.get(section, {}).get('subdir', section))

    org, repo = get_org_repo()
    manager = get_manager(GLOBALS, org, repo)

    manager.cleanup_boilerplate()

    if with_backend:
        manager.write_tf_backend_file(
            environment=environment,
            section=section,
        )

    section_values = SECTIONS.get(section, {}).get('inputs', {})
    manager.write_tfvars_file(
        # These are the values that all sections must handle
        global_values={
            "environment": environment,
            "region": GLOBALS.get('region', section_values.get('region')),
        },
        section_values=section_values,
        environment=environment,
    )
    manager.write_provider_tf_file()

    # The output subcommand's STDOUT needs to be parseable as JSON.
    suppress_verbiage = False
    if subcmd == 'output':
        suppress_verbiage = True

    # Always run "terraform init". This is safe.
    manager.run_terraform('init',
        reconfigure=reconfigure,  # This is only for the bootstrap command
        suppress_verbiage=suppress_verbiage,
    )

    suppress_input = True
    options = []
    # Force -auto-approve otherwise terraform apply/destroy will error out.
    if subcmd == 'apply':
        options.append('-auto-approve')
    elif subcmd == 'destroy':
        options.append('-auto-approve')
    elif subcmd == 'output':
        suppress_input = False

        # Always display outputs in JSON
        options.append('-json')

    # Run the command we were asked to run.
    rv = manager.run_terraform(subcmd,
        options=options,
        suppress_input=suppress_input,
        suppress_verbiage=suppress_verbiage,
    )
    # TODO: Do something here with rv - it's a CompletedProcess object
    # q.v. https://docs.python.org/3/library/subprocess.html#subprocess.CompletedProcess

    # TODO: Add a remove_outputs() to be called when destroying
    # TODO: Add a read_outputs() to be used when reading
    if subcmd == 'apply':
        manager.save_outputs(
            environment=environment,
            section=section,
        )

    manager.cleanup_boilerplate()

    # Scripts should be clear when they succeed. A visual statement is helpful.
    if not suppress_verbiage:
        print("Ok", flush=True)

if __name__ == '__main__':
    fire.Fire({
        'bootstrap': bootstrap,
        'plan': plan,
        'apply': apply,
        'destroy': destroy,
        'output': output,
    })
