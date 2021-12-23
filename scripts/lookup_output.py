#!/usr/bin/env python3
# vim: set ft=python:sw=4:ts=4

import boto3
import json

def get_outputs_key(project, environment, section):
    return f"terraform/outputs/{project}/{environment}/{section}.json"

class LookupOutput(object):
    # TODO: org, repo, and environment need to default to the current values
    def __init__(self, org=None, repo=None, environment=None, section=None, key=None):
        project = "gammaforceio/atropos_health_infra" #get_project_name()
        self.org, self.repo = project.split('/')
        self.environment = 'prod' #environment
        self.section = section
        self.key = key

    def resolve(self, bucket_name):
        key = get_outputs_key(f"{self.org}/{self.repo}", self.environment, self.section)
        s3 = boto3.resource('s3')
        blob = s3.Object(bucket_name, key).get()['Body'].read().decode('utf-8')
        data = json.loads(blob)
        value = data.get(self.key)
        if value:
            return value.get('value')
        else:
            return None
