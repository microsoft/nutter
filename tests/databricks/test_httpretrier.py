"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

import pytest
from common.httpretrier import HTTPRetrier
import requests
from requests.exceptions import HTTPError
from databricks_api import DatabricksAPI

def test__execute__no_exception__returns_value():
    retrier =  HTTPRetrier()
    value = 'hello'

    return_value = retrier.execute(_get_value, value)

    assert return_value == value

def test__execute__no_exception_named_args__returns_value():
    retrier =  HTTPRetrier()
    value = 'hello'

    return_value = retrier.execute(_get_value, return_value = value)

    assert return_value == value


def test__execute__no_exception_named_args_set_first_arg__returns_value():
    retrier =  HTTPRetrier()
    value = 'hello'

    return_values = retrier.execute(_get_values, value1 = value)

    assert return_values[0] == value
    assert return_values[1] is None


def test__execute__no_exception_named_args_set_second_arg__returns_value():
    retrier =  HTTPRetrier()
    value = 'hello'

    return_values = retrier.execute(_get_values, value2 = value)

    assert return_values[0] is None
    assert return_values[1] == value

def test__execute__raises_non_http_exception__exception_arises(mocker):
    retrier =  HTTPRetrier()
    raiser = ExceptionRaiser(0, ValueError)

    with pytest.raises(ValueError):
        return_value = retrier.execute(raiser.execute)

def test__execute__raises_500_http_exception__retries_twice_and_raises(mocker):
    retrier =  HTTPRetrier(2,1)

    db = DatabricksAPI(host='HOST',token='TOKEN')
    mock_request = mocker.patch.object(db.client.session, 'request')
    mock_resp = requests.models.Response()
    mock_resp.status_code = 500
    mock_request.return_value = mock_resp

    with pytest.raises(HTTPError):
        return_value = retrier.execute(db.jobs.get_run_output, 1)
    assert retrier._tries == 2

def test__execute__raises_403_http_exception__no_retries_and_raises(mocker):
    retrier =  HTTPRetrier(2,1)

    db = DatabricksAPI(host='HOST',token='TOKEN')
    mock_request = mocker.patch.object(db.client.session, 'request')
    mock_resp = requests.models.Response()
    mock_resp.status_code = 403
    mock_request.return_value = mock_resp

    with pytest.raises(HTTPError):
        return_value = retrier.execute(db.jobs.get_run_output, 1)
    assert retrier._tries == 0

def _get_value(return_value):
    return return_value

def _get_values(value1=None, value2=None):
    return value1, value2

class ExceptionRaiser(object):
    def __init__(self, raise_after, exception):
        self._raise_after = raise_after
        self._called = 1
        self._exception = exception

    def execute(self):
        if self._called > self._raise_after:
            raise self._exception()
        self._called = self._called + 1
        return self._called