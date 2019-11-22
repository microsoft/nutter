"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

from . import utils
from abc import ABCMeta
from .testresult import TestResults
import logging


class ExecuteNotebookResult(object):
    def __init__(self, life_cycle_state, notebook_path,
                 notebook_result, notebook_run_page_url):
        self.task_result_state = life_cycle_state
        self.notebook_path = notebook_path
        self.notebook_result = notebook_result
        self.notebook_run_page_url = notebook_run_page_url

    @classmethod
    def from_job_output(cls, job_output):
        life_cycle_state = utils.recursive_find(
            job_output, ['metadata', 'state', 'life_cycle_state'])
        notebook_path = utils.recursive_find(
            job_output, ['metadata', 'task', 'notebook_task', 'notebook_path'])
        notebook_run_page_url = utils.recursive_find(
            job_output, ['metadata', 'run_page_url'])
        notebook_result = NotebookOutputResult.from_job_output(job_output)

        return cls(life_cycle_state, notebook_path,
                   notebook_result, notebook_run_page_url)

    @property
    def is_error(self):
        # The assumption is that the task is an terminal state
        # Success state must be TERMINATED all the others are considered failures
        return self.task_result_state != 'TERMINATED'

    @property
    def is_any_error(self):
        if self.is_error:
            return True
        if self.notebook_result.is_error:
            return True
        if self.notebook_result.nutter_test_results is None:
            return True

        for test_case in self.notebook_result.nutter_test_results.results:
            if not test_case.passed:
                return True
        return False

class NotebookOutputResult(object):
    def __init__(self, result_state, exit_output, nutter_test_results):
        self.result_state = result_state
        self.exit_output = exit_output
        self.nutter_test_results = nutter_test_results

    @classmethod
    def from_job_output(cls, job_output):
        exit_output = ''
        nutter_test_results = ''
        notebook_result_state = ''
        if 'error' in job_output:
            exit_output = job_output['error']

        if 'notebook_output' in job_output:
            notebook_result_state = utils.recursive_find(
                job_output, ['metadata', 'state', 'result_state'])

            if 'result' in job_output['notebook_output']:
                exit_output = job_output['notebook_output']['result']
                nutter_test_results = cls._get_nutter_test_results(exit_output)

        return cls(notebook_result_state, exit_output, nutter_test_results)

    @property
    def is_error(self):
        # https://docs.azuredatabricks.net/dev-tools/api/latest/jobs.html#jobsrunresultstate
        return self.result_state != 'SUCCESS' and not self.is_run_from_notebook

    @property
    def is_run_from_notebook(self):
        # https://docs.azuredatabricks.net/dev-tools/api/latest/jobs.html#jobsrunresultstate
        return self.result_state == 'N/A'

    @classmethod
    def _get_nutter_test_results(cls, exit_output):
        nutter_test_results = cls._to_nutter_test_results(exit_output)
        if nutter_test_results is None:
            return None
        return nutter_test_results

    @classmethod
    def _to_nutter_test_results(cls, exit_output):
        if not exit_output:
            return None
        try:
            return TestResults().deserialize(exit_output)
        except Exception as ex:
            error = 'error while creating result from {}. Error: {}'.format(
                ex, exit_output)
            logging.debug(error)
            return None


class WorkspacePath(object):
    def __init__(self, notebooks, directories):
        self.notebooks = notebooks
        self.directories = directories
        self.test_notebooks = self._set_test_notebooks()

    @classmethod
    def from_api_response(cls, objects):
        notebooks = cls._set_notebooks(objects)
        directories = cls._set_directories(objects)
        return cls(notebooks, directories)

    @classmethod
    def _set_notebooks(cls, objects):
        if 'objects' not in objects:
            return []
        return [NotebookObject(object['path']) for object in objects['objects']
                if object['object_type'] == 'NOTEBOOK']

    @classmethod
    def _set_directories(cls, objects):
        if 'objects' not in objects:
            return []
        return [Directory(object['path']) for object in objects['objects']
                if object['object_type'] == 'DIRECTORY']

    def _set_test_notebooks(self):
        return [notebook for notebook in self.notebooks
                if notebook.is_test_notebook]


class WorkspaceObject():
    __metaclass__ = ABCMeta

    def __init__(self, path):
        self.path = path


class NotebookObject(WorkspaceObject):
    def __init__(self, path):
        self.name = self._get_notebook_name_from_path(path)
        super().__init__(path)

    def _get_notebook_name_from_path(self, path):
        segments = path.split('/')
        if len(segments) == 0:
            raise ValueError('Invalid path. Path must start /')
        name = segments[len(segments)-1]
        return name

    @property
    def is_test_notebook(self):
        return self._is_valid_test_name(self.name)

    def _is_valid_test_name(self, name):
        if name is None:
            return False

        return name.lower().startswith('test_')


class Directory(WorkspaceObject):
    def __init__(self, path):
        super().__init__(path)
