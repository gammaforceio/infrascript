# vim: set ft=python:sw=4:ts=4

import pytest_describe

import sys
sys.path.insert(0, '/opt/infra/lib')
import main

# This is a test that simply verifies main.py loads.
def describe_dummy_test():
    def is_truthy():
        assert True == True
