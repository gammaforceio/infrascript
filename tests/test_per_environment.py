# vim: set ft=python:sw=4:ts=4

import pytest

from infrascript.manager import (
    get_manager,
)
from infrascript.per_environment import (
    EnvironmentNotFoundError,
    PerEnvironment,
)

def manager():
    return get_manager(
        GLOBALS={
            'type': 'aws',
            'backend': {
                'bucket_name': 'some-bucket',
            },
        },
        org='org1',
        repo='repo1',
    )

def describe_PerEnvironment():
    def environment_found():
        value = PerEnvironment(
            dev='abc',
        )

        rv = value.resolve(
            manager=manager(),
            environment='dev',
        )

        assert rv == 'abc'

    def default_defined():
        value = PerEnvironment(
            __DEFAULT__='abc',
        )

        rv = value.resolve(
            manager=manager(),
            environment='env1',
        )

        assert rv == 'abc'

    def env_not_found():
        value = PerEnvironment(
            dev='abc',
        )

        with pytest.raises(EnvironmentNotFoundError) as e:
            rv = value.resolve(
                manager=manager(),
                environment='prod',
            )

        assert e.value.args[0] == "prod not found"
