# vim: set ft=python:sw=4:ts=4

import pytest_describe

import sys
sys.path.insert(0, '/opt/infra/lib')

from infra import (
    get_org_repo,
)
from manager import (
    get_manager,
)
from lookup_output import (
    LookupOutput,
)
from per_environment import (
    PerEnvironment,
)

def describe_get_org_repo():
    def without_envvar(monkeypatch):
        monkeypatch.delenv('SCM_PROJECT', raising=False)
        org, repo = get_org_repo()
        assert org == None and repo == None

    def with_empty_envvar(monkeypatch):
        monkeypatch.setenv('SCM_PROJECT', '')
        org, repo = get_org_repo()
        assert org == '' and repo == ''

    def with_envvar_no_slashes(monkeypatch):
        monkeypatch.setenv('SCM_PROJECT', 'hello')
        org, repo = get_org_repo()
        assert org == 'hello' and repo == ''

    def with_envvar_one_slash(monkeypatch):
        monkeypatch.setenv('SCM_PROJECT', 'org1/repo1')
        org, repo = get_org_repo()
        assert org == 'org1' and repo == 'repo1'

    # This is really an error, but things work
    def with_envvar_two_slashes(monkeypatch):
        monkeypatch.setenv('SCM_PROJECT', 'with/two/slashes')
        org, repo = get_org_repo()
        assert org == 'with' and repo == 'two'

def describe_resolve_section_values():
    def _run_resolve_section_values(section_values):
        manager = get_manager(
            GLOBALS={
                'type': 'aws',
                'backend': {
                    'bucket_name': 'some-bucket',
                },
            },
            org='org1',
            repo='repo1',
        )
        manager.resolve_section_values(
            section_values=section_values,
            environment='prod',
        )

    def no_values():
        section_values = {}

        _run_resolve_section_values(section_values)

        assert len(section_values.keys()) == 0

    def constant_value():
        section_values = {
            'x': 1,
        }

        _run_resolve_section_values(section_values)

        assert section_values == { 'x': 1 }

    def constant_value_2_levels():
        section_values = {
            'x': { 'y': 1 },
        }

        _run_resolve_section_values(section_values)

        assert section_values == { 'x': { 'y': 1 } }

    def lookup_output(monkeypatch):
        def myresolve(self, bucket_name, org, repo, environment):
            return 'value1'
        monkeypatch.setattr(LookupOutput, 'resolve', myresolve)

        section_values = {
            'x': LookupOutput(
                section='s1',
                key='k1',
            ),
        }

        _run_resolve_section_values(section_values)

        assert section_values == { 'x': 'value1' }

    def lookup_output_2_levels_dict(monkeypatch):
        def myresolve(self, bucket_name, org, repo, environment):
            return 'value1'
        monkeypatch.setattr(LookupOutput, 'resolve', myresolve)

        section_values = {
            'x': {
                'y': LookupOutput(
                    section='s1',
                    key='k1',
                ),
            },
        }

        _run_resolve_section_values(section_values)

        assert section_values == { 'x': { 'y': 'value1' } }

    def lookup_output_2_levels_list(monkeypatch):
        def myresolve(self, bucket_name, org, repo, environment):
            return 'value1'
        monkeypatch.setattr(LookupOutput, 'resolve', myresolve)

        section_values = {
            'x': [
                LookupOutput(
                    section='s1',
                    key='k1',
                ),
            ],
        }

        _run_resolve_section_values(section_values)

        assert section_values == { 'x': [ 'value1' ] }

    def per_environment_name_found():
        section_values = {
            'x': PerEnvironment(
                prod=1,
            ),
        }

        _run_resolve_section_values(section_values)

        assert section_values == { 'x': 1 }

    def per_environment_default_found():
        section_values = {
            'x': PerEnvironment(
                __DEFAULT__=1,
            ),
        }

        _run_resolve_section_values(section_values)

        assert section_values == { 'x': 1 }

    def per_environment_lookup_output(monkeypatch):
        def myresolve(self, bucket_name, org, repo, environment):
            return 'value1'
        monkeypatch.setattr(LookupOutput, 'resolve', myresolve)

        section_values = {
            'x': PerEnvironment(
                __DEFAULT__=LookupOutput(
                    section='s1',
                    key='k1',
                ),
            ),
        }

        _run_resolve_section_values(section_values)

        assert section_values == { 'x': 'value1' }
