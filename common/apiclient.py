"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

import uuid
import time
from databricks_api import DatabricksAPI
from . import authconfig as cfg, utils
from .apiclientresults import ExecuteNotebookResult, WorkspacePath
from .httpretrier import HTTPRetrier
import logging

DEFAULT_POLL_WAIT_TIME = 5
MIN_TIMEOUT = 10

def databricks_client():

    db = DatabricksAPIClient()

    return db


class DatabricksAPIClient(object):
    """
    """

    def __init__(self):
        config = cfg.get_auth_config()
        self.min_timeout = MIN_TIMEOUT

        if config is None:
            raise InvalidConfigurationException

        # TODO: remove the dependency with this API, an instead use httpclient/requests
        db = DatabricksAPI(host=config.host,
                           token=config.token)
        self.inner_dbclient = db

        # The retrier uses the recommended defaults
        # https://docs.microsoft.com/en-us/azure/databricks/dev-tools/api/latest/jobs
        self._retrier = HTTPRetrier()

    def list_notebooks(self, path):
        workspace_objects = self.list_objects(path)
        notebooks = workspace_objects.notebooks
        return notebooks

    def list_objects(self, path):
        objects = self.inner_dbclient.workspace.list(path)
        logging.debug('Creating WorkspacePath for path {}'.format(path))
        logging.debug('List response: \n\t{}'.format(objects))

        workspace_path_obj = WorkspacePath.from_api_response(objects)
        logging.debug('WorkspacePath created')

        return workspace_path_obj

    def execute_notebook(self, notebook_path, cluster_id, timeout=120,
                         pull_wait_time=DEFAULT_POLL_WAIT_TIME,
                         notebook_params=None):
        if not notebook_path:
            raise ValueError("empty path")
        if not cluster_id:
            raise ValueError("empty cluster id")
        if timeout < self.min_timeout:
            raise ValueError(
                "Timeout must be greater than {}".format(self.min_timeout))
        if notebook_params is not None:
            if not isinstance(notebook_params, dict):
                raise ValueError("Parameters must be in the form of a dictionary (See #run-single-test-notebook section in README)")
        if pull_wait_time <= 1:
            pull_wait_time = DEFAULT_POLL_WAIT_TIME

        name = str(uuid.uuid1())
        ntask = self.__get_notebook_task(notebook_path, notebook_params)

        runid = self._retrier.execute(self.inner_dbclient.jobs.submit_run,
                                      run_name=name,
                                      existing_cluster_id=cluster_id,
                                      notebook_task=ntask,
                                      )

        if 'run_id' not in runid:
            raise NotebookTaskRunIDMissingException

        life_cycle_state, output = self.__pull_for_output(
            runid['run_id'], timeout, pull_wait_time)

        return ExecuteNotebookResult.from_job_output(output)

    def __pull_for_output(self, run_id, timeout, pull_wait_time):
        timedout = time.time() + timeout
        output = {}
        while time.time() < timedout:
            output = self._retrier.execute(
                self.inner_dbclient.jobs.get_run_output, run_id)
            logging.debug(output)

            lcs = utils.recursive_find(
                output, ['metadata', 'state', 'life_cycle_state'])

            # As per:
            # https://docs.azuredatabricks.net/api/latest/jobs.html#jobsrunlifecyclestate
            # All these are terminal states
            if lcs == 'TERMINATED' or lcs == 'SKIPPED' or lcs == 'INTERNAL_ERROR':
                logging.debug('Terminal state returned. {}'.format(lcs))
                return lcs, output
            logging.debug('Not terminal state returned. Sleeping {}s'.format(pull_wait_time))
            time.sleep(pull_wait_time)

        self._raise_timeout(output)

    def _raise_timeout(self, output):
        run_page_url = utils.recursive_find(
            output, ['metadata', 'run_page_url'])
        raise TimeOutException(
            """ Timeout while waiting for the result of a test.\n
                Check the status of the execution\n
                Run page URL: {} """.format(run_page_url))

    def __get_notebook_task(self, path, params):
        ntask = {}
        ntask['notebook_path'] = path
        base_params = []
        if params is not None:
            for key in params:
                param = {}
                param['key'] = key
                param['value'] = params[key]
                base_params.append(param)
            ntask['base_parameters'] = base_params

        return ntask


class NotebookTaskRunIDMissingException(Exception):
    pass


class InvalidConfigurationException(Exception):
    pass


class TimeOutException(Exception):
    pass
