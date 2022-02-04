# vim: set ft=python:sw=4:ts=4

import pytest_describe

import sys
sys.path.insert(0, '/opt/infra/lib')
from lookup_output import get_outputs_key

def describe_get_outputs_key():
    def basic_values():
        rv = get_outputs_key("o1", "r1", "e1", "s1")
        assert rv == "terraform/outputs/o1/r1/e1/s1.json"
