"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

import logging
from time import sleep
from requests.exceptions import HTTPError


class HTTPRetrier(object):
    def __init__(self, max_retries=20, delay=30):
        self._max_retries = max_retries
        self._delay = delay
        self._tries = 0

    def execute(self, function, *args, **kwargs):
        waitfor = self._delay
        retry = True
        self._tries = 0
        while retry:
            try:
                retry = self._tries < self._max_retries
                logging.debug(
                    'Executing function with HTTP retry policy. Max tries:{}  delay:{}'
                    .format(self._max_retries, self._delay))

                return function(*args, **kwargs)
            except HTTPError as exc:
                logging.debug("Error: {0}".format(str(exc)))
                if not retry:
                    raise
                if isinstance(exc.response.status_code, int):
                    if exc.response.status_code < 500:
                        raise
            if retry:
                logging.debug(
                    'Retrying in {0}s, {1} of {2} retries'
                    .format(str(waitfor), str(self._tries+1), str(self._max_retries)))
                sleep(waitfor)
            self._tries = self._tries + 1
