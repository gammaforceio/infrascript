# vim: set ft=python:sw=4:ts=4

import boto3
import json

def get_outputs_key(org, repo, environment, section):
    return f"terraform/outputs/{org}/{repo}/{environment}/{section}.json"

class LookupOutput(object):
    def __init__(self, section, key, org=None, repo=None, environment=None):
        self.org = org
        self.repo = repo
        self.environment = environment
        self.section = section
        self.key = key

    def resolve(self, bucket_name, org, repo, environment):
        key = get_outputs_key(
            self.org or org,
            self.repo or repo,
            self.environment or environment,
            self.section,
        )
        resource = self.__resource()
        blob = resource.Object(bucket_name, key).get()['Body'].read().decode('utf-8')
        data = json.loads(blob)
        return data.get(self.key, {}).get('value')

class LookupOutputAWS(LookupOutput):
    def __resource(self):
        return boto3.resource('s3')

class LookupOutputGCP(LookupOutput):
    def __resource(self):
        return boto3.resource('s3') # Add endpoints here
