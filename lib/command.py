# vim: set ft=python:sw=4:ts=4

import subprocess

# TODO: This needs to handle and propagate failure
def run_command(cmd, stream=False):
    # We want to stream the results back to the user. We want to return
    # success or failure to the invoker.
    if stream:
        return subprocess.run(
            cmd,
            capture_output=False,
        )
    # We're not streaming, so capture and return the output to the invoker.
    else:
        return subprocess.Popen(
            cmd, stdout=subprocess.PIPE,
        ).communicate()[0].rstrip().decode('utf-8')
