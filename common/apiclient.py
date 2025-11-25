"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

import uuid
import datetime
from .apiclientresults import ExecuteNotebookResult, WorkspacePath
import logging
from .utils import get_nutter_version

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.jobs import NotebookTask, Task, JobEnvironment
from databricks.sdk.service.compute import Environment

MIN_TIMEOUT = 10


def databricks_client():
    return DatabricksAPIClient()


class DatabricksAPIClient(object):
    """
    """

    def __init__(self):
        self.min_timeout = MIN_TIMEOUT
        self.dbclient = WorkspaceClient(product="nutter", product_version=get_nutter_version())

    def list_notebooks(self, path):
        workspace_objects = self.list_objects(path)
        notebooks = workspace_objects.notebooks
        return notebooks

    def list_objects(self, path):
        objects = self.dbclient.workspace.list(path)
        logging.debug(f'Creating WorkspacePath for path {path}')
        logging.debug(f'List response: \n\t{objects}')

        workspace_path_obj = WorkspacePath.from_api_response(objects)
        logging.debug('WorkspacePath created')

        return workspace_path_obj

    def get_cluster_id_by_name(self, cluster_name):
        """
        Get cluster ID by cluster name (case-insensitive).
        
        Args:
            cluster_name: The name of the cluster to find
            
        Returns:
            The cluster ID if found
            
        Raises:
            ValueError: If cluster name is empty, not found, or multiple clusters with the same name exist
        """
        if not cluster_name:
            raise ValueError("empty cluster name")
        
        # List all clusters and filter by name (case-insensitive)
        clusters = list(self.dbclient.clusters.list())
        cluster_name_lower = cluster_name.lower()
        matching_clusters = [c for c in clusters if c.cluster_name and c.cluster_name.lower() == cluster_name_lower]
        
        if len(matching_clusters) == 0:
            raise ValueError(f"No cluster found with name '{cluster_name}'")
        elif len(matching_clusters) > 1:
            raise ValueError(f"Multiple clusters found with name '{cluster_name}'. Please use cluster_id instead.")
        
        return matching_clusters[0].cluster_id

    def execute_notebook(self, notebook_path, cluster_id=None, timeout=120,
                         notebook_params=None, serverless=None):
        """
        Execute a notebook on either a cluster or serverless compute.
        
        Args:
            notebook_path: Path to the notebook to execute
            cluster_id: Cluster ID to run on (mutually exclusive with serverless)
            timeout: Execution timeout in seconds (default: 120)
            notebook_params: Parameters to pass to the notebook (dict)
            serverless: Serverless environment version as integer (e.g., 1) (mutually exclusive with cluster_id)
            
        Raises:
            ValueError: If validation fails
        """
        if not notebook_path:
            raise ValueError("empty path")
        
        # Validate that either cluster_id or serverless is provided, but not both
        if cluster_id is None and serverless is None:
            raise ValueError("either cluster_id or serverless must be specified")
        if cluster_id is not None and serverless is not None:
            raise ValueError("cannot specify both cluster_id and serverless")
        
        # Validate cluster_id is not empty if provided
        if cluster_id is not None and not cluster_id:
            raise ValueError("empty cluster id")
        
        # Validate serverless is an integer if provided
        if serverless is not None:
            if not isinstance(serverless, int):
                raise ValueError("serverless must be an integer")
            
        if timeout < self.min_timeout:
            raise ValueError(
                f"Timeout must be greater than {self.min_timeout}")
        if notebook_params is not None:
            if not isinstance(notebook_params, dict):
                raise ValueError("Parameters must be in the form of a dictionary (See "
                                 "#run-single-test-notebook section in README)")

        name = str(uuid.uuid1())
        
        # Configure task based on compute type
        if serverless is not None:
            # Use serverless compute with environment
            # Convert integer to string for environment_version
            ntask = Task(
                notebook_task=NotebookTask(notebook_path, base_parameters=notebook_params),
                environment_key="serverless",
                task_key="a"
            )
            
            # Define serverless environment
            environments = [
                JobEnvironment(
                    environment_key="serverless",
                    spec=Environment(environment_version=str(serverless))
                )
            ]
            
            run = self.dbclient.jobs.submit_and_wait(
                tasks=[ntask],
                run_name=name,
                environments=environments,
                timeout=datetime.timedelta(seconds=timeout)
            )
        else:
            # Use existing cluster
            ntask = Task(
                notebook_task=NotebookTask(notebook_path, base_parameters=notebook_params),
                existing_cluster_id=cluster_id,
                task_key="a"
            )
            
            run = self.dbclient.jobs.submit_and_wait(
                tasks=[ntask],
                run_name=name,
                timeout=datetime.timedelta(seconds=timeout)
            )

        return ExecuteNotebookResult.from_job_output(run, self.dbclient)


class InvalidConfigurationException(Exception):
    pass


class TimeOutException(Exception):
    pass
