# vim: set ft=python:sw=4:ts=4

import os
from tempfile import NamedTemporaryFile

def write_to_named_tempfile(content, suffix):
    tempfile = NamedTemporaryFile(
        dir='.',
        prefix='boilerplate-',
        suffix=suffix,
        delete=False,
    )
    with open(tempfile.name, 'w') as fh:
        fh.write(content)
        fh.flush()

    return os.path.basename(tempfile.name)
