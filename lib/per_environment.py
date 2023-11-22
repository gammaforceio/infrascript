# vim: set ft=python:sw=4:ts=4

# This takes a keyword mapping of environment name and value, which could be a
# LookupOutput object. The environment is either an environment name or the
# special values:
#   __DEFAULT__ - 
#
# If an environment is provided and it cannot be found, then an
# Infrascript::EnvironmentNotFound exception will be thrown.

class EnvironmentNotFoundError(Exception):
    pass

class PerEnvironment(object):
    def __init__(self, **kwargs):
        self._envmap = kwargs

    def resolve(self, manager, environment):
        if environment in self._envmap:
            return self._envmap[environment]

        if '__DEFAULT__' in self._envmap:
            return self._envmap['__DEFAULT__']
        
        raise EnvironmentNotFoundError(
            f"{environment} not found"
        )
