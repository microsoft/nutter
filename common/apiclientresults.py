"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""
from typing import Iterator, Optional, Union

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.jobs import Run, RunResultState

from . import utils
from abc import ABCMeta
from .testresult import TestResults
import logging

from databricks.sdk.service.workspace import ObjectType, ObjectInfo


class NotebookOutputResult(object):
    def __init__(self, result_state: Union[RunResultState, str, None], exit_output, nutter_test_results):
        if result_state is None:
            self.result_state = None
        elif isinstance(result_state, str):
            self.result_state = result_state
        else:
            self.result_state = result_state.value
        self.exit_output = exit_output
        self.nutter_test_results = nutter_test_results

    @classmethod
    def from_job_output(cls, run: Run, dbclient: WorkspaceClient):
        ntb_task = run.tasks[0]
        run_id = ntb_task.run_id

        output = dbclient.jobs.get_run_output(run_id)

        exit_output = ''
        nutter_test_results = ''
        notebook_result_state = ntb_task.state.result_state
        if output.error:
            exit_output = output

        if output.notebook_output is not None and output.notebook_output.result is not None:
            exit_output = output.notebook_output.result
            nutter_test_results = cls._get_nutter_test_results(exit_output)

        return cls(notebook_result_state, exit_output, nutter_test_results)

    @property
    def is_error(self):
        # https://docs.azuredatabricks.net/dev-tools/api/latest/jobs.html#jobsrunresultstate
        return self.result_state != 'SUCCESS' and \
            self.result_state != 'SUCCESS_WITH_FAILURES' and \
            not self.is_run_from_notebook

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
            error = f'error while creating result from {ex}. Error: {exit_output}'
            logging.debug(error)
            return None


class ExecuteNotebookResult(object):
    def __init__(self, task_result_state: Union[RunResultState, str, None], notebook_path: str,
                 notebook_result: NotebookOutputResult, notebook_run_page_url):
        if task_result_state is None:
            self.task_result_state = None
        elif isinstance(task_result_state, str):
            self.task_result_state = task_result_state
        else:
            self.task_result_state = task_result_state.value
        self.notebook_path = notebook_path
        self.notebook_result = notebook_result
        self.notebook_run_page_url = notebook_run_page_url

    @classmethod
    def from_job_output(cls, run: Run, dbclient: WorkspaceClient):
        notebook_result = NotebookOutputResult.from_job_output(run, dbclient)

        return cls(run.state.life_cycle_state, run.tasks[0].notebook_task.notebook_path,
                   notebook_result, run.run_page_url)

    @property
    def is_error(self) -> bool:
        # task_result_state now contains lifecycle state
        # TERMINATED is the normal completion state, other states indicate issues
        err = self.task_result_state not in ['TERMINATED', 'SUCCESS', 'SUCCESS_WITH_FAILURES', None]
        return err

    @property
    def is_any_error(self):
        if self.is_error:
            logging.debug(f"is_error: {self}")
            return True
        if self.notebook_result.is_error:
            logging.debug(f"self.notebook_result.is_error: {self}")
            return True
        if self.notebook_result.nutter_test_results is None:
            logging.debug(f"self.notebook_result.nutter_test_results: {self}")
            return True

        for test_case in self.notebook_result.nutter_test_results.results:
            if not test_case.passed:
                logging.debug(f"!test_case.passed: {test_case}, {self}")
                return True

        return False


class WorkspacePath(object):
    def __init__(self, notebooks, directories):
        self.notebooks = notebooks
        self.directories = directories
        self.test_notebooks = self._set_test_notebooks()

    @classmethod
    def from_api_response(cls, objects: Iterator[ObjectInfo]):
        notebooks = cls._set_notebooks(objects)
        directories = cls._set_directories(objects)
        return cls(notebooks, directories)

    @classmethod
    def _set_notebooks(cls, objects: Iterator[ObjectInfo]):
        return [NotebookObject(obj.path) for obj in objects
                if obj.object_type == ObjectType.NOTEBOOK]

    @classmethod
    def _set_directories(cls, objects: Iterator[ObjectInfo]):
        return [Directory(obj.path) for obj in objects
                if obj.object_type == ObjectType.DIRECTORY]

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
        name = segments[-1]
        return name

    @property
    def is_test_notebook(self):
        return utils.contains_test_prefix_or_suffix(self.name)


class Directory(WorkspaceObject):
    def __init__(self, path):
        super().__init__(path)
