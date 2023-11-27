# vim: set ft=python:sw=4:ts=4

from collections.abc import Mapping, Sequence, Set
#from functools import reduce
import json
import os

from ..command import run_command
from ..lookup_output import LookupOutput, get_outputs_key
from ..per_environment import PerEnvironment
from ..tempfile import write_to_named_tempfile

class Manager:
    def __init__(self, GLOBALS, org, repo):
        self.GLOBALS = GLOBALS
        self.org = org
        self.repo = repo

        self.tfvars_filename = None

    # TODO: Refactor this to use Path() instead of os.system()
    def cleanup_boilerplate(self):
        os.system('rm -f boilerplate-*')
        os.system('rm -rf .terraform')

    def write_tfvars_file(self,
        global_values, section_values, environment,
    ):
        # This modifies section_values's keys and values, so it does not need to
        # be returned. The actual section_values dict object is unchanged, so
        # Python's pass-by-value semantics are preserved.
        self.resolve_section_values(
            section_values=section_values,
            environment=environment,
        )

        output = global_values.copy()

        # Allow overriding the global region on a per-section basis
        output['region'] = output.get('region', self.GLOBALS['region'])

        output.update(section_values)

        self.tfvars_filename = write_to_named_tempfile(
            json.dumps(output),
            suffix='.tfvars.json',
        )

    # q.v. https://learn.hashicorp.com/tutorials/terraform/automate-terraform
    def run_terraform(self,
        subcmd, suppress_input=True, reconfigure=False,
        options=[], stream_output=True, suppress_verbiage=False,
    ):
        cmd = ['terraform']

        cmd.append(subcmd)

        if reconfigure:
            cmd.append('-reconfigure')
            cmd.append('-force-copy')
        elif suppress_input:
            # We're running in automation, so always suppress -input
            # TODO: Figure out why this broke using --reconfigure
            cmd.append('-input=false')

        cmd = cmd + options

        # The output subcommand cannot handle the -var-file parameter.
        if subcmd != 'output':
            cmd.append(f'-var-file={self.tfvars_filename}')

        # TODO: Put this behind an "if debug"
        #print(f"{' '.join(cmd)}", flush=True)

        # These lines are here in case you want to pause right before execution.
        #import time
        #time.sleep(1000)

        if stream_output and not suppress_verbiage:
            print(f"Running {subcmd}", flush=True)

        return run_command(cmd, stream=stream_output and subcmd != 'init')

    def resolve_section_values(self,
        section_values, environment,
    ):
        # Full walking code is at https://code.activestate.com/recipes/577982/.
        # This is adapted to walk over and modify section_values.
        string_types = (str, bytes)
        iteritems = lambda x: getattr(x, 'iteritems', x.items)()
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
                    manager=self,
                    environment=environment,
                )

            if isinstance(value, LookupOutput):
                value = value.resolve(
                    manager=self,
                    environment=environment,
                    bucket_name=self.GLOBALS['backend']['bucket_name'],
                    org=self.org,
                    repo=self.repo,
                )

            __set(section_values, path, value)

        return section_values

    def save_outputs(self, environment, section):
        bucket = self.GLOBALS['backend']['bucket_name']
        key = get_outputs_key(self.org, self.repo, environment, section)
        outputs = self.run_terraform("output",
            options=['-json'],
            suppress_input=False,
            stream_output=False,
        )

        self.write_to_bucket(bucket, key, content=outputs)
