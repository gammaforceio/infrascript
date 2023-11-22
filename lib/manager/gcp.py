# vim: set ft=python:sw=4:ts=4

from .base import Manager

class GCPManager(Manager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def write_tf_backend_file(self, bucket, key, contents):
        raise NotImplemented("GCPManager.write_tf_backend_file()")

    def write_provider_tf_file(self, bucket, key, contents):
        raise NotImplemented("GCPManager.write_provider_tf_file()")

    def write_to_bucket(self, bucket, key, contents):
        raise NotImplemented("GCPManager.write_to_bucket()")
