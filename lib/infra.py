#!/usr/bin/env python3
# vim: set ft=python:sw=4:ts=4

import argparse
from collections.abc import Mapping, Sequence, Set
#from functools import reduce
import os
import sys

from lookup_output import LookupOutput
from per_environment import PerEnvironment

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

def get_org_repo():
    project = os.getenv('SCM_PROJECT')
    if project is None:
        return None, None
    vals = project.split('/')
    vals.extend(['', ''])
    return vals[0:2]
