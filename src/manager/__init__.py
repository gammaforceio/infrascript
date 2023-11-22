# vim: set ft=python:sw=4:ts=4

from .aws import AWSManager
from .gcp import GCPManager

def get_manager(GLOBALS, org, repo):
    iaas = GLOBALS['type'].lower()
    if iaas == 'aws':
        return AWSManager(GLOBALS, org, repo)
    if iaas == 'gcp':
        return GCPManager(GLOBALS, org, repo)
    raise ValueError(f"Unknown IaaS: {iaas}")
