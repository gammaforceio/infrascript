# vim: set ft=python:sw=4:ts=4

import boto3

from .base import Manager
from ..tempfile import write_to_named_tempfile

class AWSManager(Manager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def write_tf_backend_file(self,
        environment, section,
    ):
        bucket = self.GLOBALS['backend']['bucket_name']
        dynamodb_table = self.GLOBALS['backend']['dynamodb_table']

        region = self.GLOBALS['region']

        key = f"terraform/state/{self.org}/{self.repo}/{environment}/{section}.tfstate"

        # The doubled-braces are to handle how f-strings deal with them.
        # Otherwise, this will be a syntax error.
        return write_to_named_tempfile(f"""
terraform {{
    backend "s3" {{
        bucket = "{bucket}"
        key = "{key}"
        region = "{region}"
        dynamodb_table = "{dynamodb_table}"
    }}
}}
        """, suffix='.tf')

    def write_provider_tf_file(self):
        # The doubled-braces are to handle how f-strings deal with them.
        # Otherwise, this will be a syntax error.
        return write_to_named_tempfile(f"""
variable "region" {{
    type = string
    nullable = false
}}

provider aws {{
    region = var.region
}}

data "aws_caller_identity" "current" {{}}
        """, suffix='.tf')

    def read_from_bucket(self, bucket, key):
        return boto3.resource('s3').Object(bucket_name, key).get()['Body'].read().decode('utf-8')

    def write_to_bucket(self, bucket, key, content):
        boto3.resource('s3').Object(bucket, key).put(Body=content)
        print(f"Outputs saved to s3://{bucket}/{key}", flush=True)
