# vim: set ft=python:sw=4:ts=4

import pytest

from infrascript.per_environment import (
    EnvironmentNotFoundError,
    PerEnvironment,
)

def describe_PerEnvironment():
    def environment_found():
        value = PerEnvironment(
            dev='abc',
        )

        rv = value.resolve(environment='dev')

        assert rv == 'abc'

    def default_defined():
        value = PerEnvironment(
            __DEFAULT__='abc',
        )

        rv = value.resolve(environment='env1')

        assert rv == 'abc'

    def env_not_found():
        value = PerEnvironment(
            dev='abc',
        )

        with pytest.raises(EnvironmentNotFoundError) as e:
            rv = value.resolve(environment='prod')

        assert e.value.args[0] == "prod not found"
