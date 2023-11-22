# vim: set ft=python:sw=4:ts=4

import infrascript.main

# This is a test that simply verifies main.py loads.
def describe_dummy_test():
    def is_truthy():
        assert True == True
