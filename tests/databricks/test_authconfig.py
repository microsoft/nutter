"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

import pytest
import os
from common import authconfig as auth

def test_tokenhostset_okay(mocker):
    mocker.patch.dict(os.environ,{'DATABRICKS_HOST':'host'})
    mocker.patch.dict(os.environ,{'DATABRICKS_TOKEN':'token'})

    config = auth.get_auth_config()
    # Assert
    assert config != None
    assert config.host == 'host'
    assert config.token == 'token'

def test_onlytokenset_none(mocker):
    mocker.patch.dict(os.environ,{'DATABRICKS_HOST':''})
    mocker.patch.dict(os.environ,{'DATABRICKS_TOKEN':'token'})

    config = auth.get_auth_config()
    # Assert
    assert config == None

def test_tokenhostsetemtpy_none(mocker):
    mocker.patch.dict(os.environ,{'DATABRICKS_HOST':''})
    mocker.patch.dict(os.environ,{'DATABRICKS_TOKEN':''})

    config = auth.get_auth_config()
    # Assert
    assert config == None

def test_onlyhostset_none(mocker):
    mocker.patch.dict(os.environ,{'DATABRICKS_HOST':'host'})
    mocker.patch.dict(os.environ,{'DATABRICKS_TOKEN':''})

    config = auth.get_auth_config()
    # Assert
    assert config == None

def test_tokenhostinsecureset_okay(mocker):
    mocker.patch.dict(os.environ,{'DATABRICKS_HOST':'host'})
    mocker.patch.dict(os.environ,{'DATABRICKS_TOKEN':'token'})
    mocker.patch.dict(os.environ,{'DATABRICKS_INSECURE':'insecure'})

    config = auth.get_auth_config()

    # Assert
    assert config != None
    assert config.host == 'host'
    assert config.token == 'token'
    assert config.insecure == 'insecure'
