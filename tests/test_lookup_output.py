# vim: set ft=python:sw=4:ts=4

from infrascript.lookup_output import get_outputs_key

def describe_get_outputs_key():
    def basic_values():
        rv = get_outputs_key("o1", "r1", "e1", "s1")
        assert rv == "terraform/outputs/o1/r1/e1/s1.json"
