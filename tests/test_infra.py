import pytest_describe

import sys
sys.path.insert(0, '/opt/infra/lib')
from infra import get_org_repo

def describe_get_org_repo():
    def without_envvar(monkeypatch):
        monkeypatch.delenv('SCM_PROJECT', raising=False)
        org, repo = get_org_repo()
        assert org == None and repo == None

    def with_empty_envvar(monkeypatch):
        monkeypatch.setenv('SCM_PROJECT', '')
        org, repo = get_org_repo()
        assert org == '' and repo == ''

    def with_envvar_no_slashes(monkeypatch):
        monkeypatch.setenv('SCM_PROJECT', 'hello')
        org, repo = get_org_repo()
        assert org == 'hello' and repo == ''

    def with_envvar_one_slash(monkeypatch):
        monkeypatch.setenv('SCM_PROJECT', 'org1/repo1')
        org, repo = get_org_repo()
        assert org == 'org1' and repo == 'repo1'

    # This is really an error, but things work
    def with_envvar_two_slashes(monkeypatch):
        monkeypatch.setenv('SCM_PROJECT', 'with/two/slashes')
        org, repo = get_org_repo()
        assert org == 'with' and repo == 'two'
