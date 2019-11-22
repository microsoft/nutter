"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

import os
from abc import abstractmethod, ABCMeta

def get_auth_config():
    """
    """

    providers = (EnvVariableAuthConfigProvider(),)

    for provider in providers:
        config = provider.get_auth_config()
        if config is not None and config.is_valid:
            return config
    return None

class DatabricksApiAuthConfigProvider(object):
    """
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def get_auth_config(self):
        pass

class DatabricksApiAuthConfig(object):
    def __init__(self, host, token, insecure):
        self.host = host
        self.token = token
        self.insecure = insecure

    @property
    def is_valid(self):
        if self.host == '' or self.token == '':
            return False

        return self.host is not None and self.token is not None

class EnvVariableAuthConfigProvider(DatabricksApiAuthConfigProvider):
    """
    Loads token auth configuration from environment variables.
    """

    def get_auth_config(self):
        host = os.environ.get('DATABRICKS_HOST')
        token = os.environ.get('DATABRICKS_TOKEN')
        insecure = os.environ.get('DATABRICKS_INSECURE')
        config = DatabricksApiAuthConfig(host, token, insecure)
        if config.is_valid:
            return config
        return None
