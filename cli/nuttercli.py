"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

import fire
import logging
import os
import datetime

import common.api as api
from common.apiclient import InvalidConfigurationException
from common.utils import get_nutter_version

import common.resultsview as view
from .eventhandlers import ConsoleEventHandler
from .resultsvalidator import ExecutionResultsValidator
from .reportsman import ReportWriters
from . import reportsman as reports


def get_cli_header():
    header = f'Nutter Version {get_nutter_version()}\n'
    header += '+' * 50
    header += '\n'

    return header


class NutterCLI(object):

    def __init__(self, debug=False, log_to_file=False, version=False):
        self._logger = logging.getLogger('NutterCLI')
        self._handle_show_version(version)

        # CLI only logger so the output is not dictated
        # by the logging configuration of all the other components
        self._set_debugging(debug, log_to_file)
        self._print_cli_header()
        self._set_nutter(debug)
        super().__init__()

    def run(self, test_pattern, cluster_id=None, cluster_name=None, serverless=None,
            timeout=120, junit_report=False,
            tags_report=False, max_parallel_tests=1,
            recursive=False, notebook_params=None):
        try:
            # Validate compute configuration
            compute_options = [cluster_id is not None, cluster_name is not None, serverless is not None]
            compute_count = sum(compute_options)
            
            if compute_count == 0:
                self._logger.fatal("Must specify one of: --cluster_id, --cluster_name, or --serverless")
                exit(1)
            
            if compute_count > 1:
                self._logger.fatal("Cannot specify multiple compute options. Use only one of: --cluster_id, --cluster_name, or --serverless")
                exit(1)
            
            # If cluster_name is provided, resolve it to cluster_id
            if cluster_name is not None:
                logging.debug(f"Resolving cluster name '{cluster_name}' to cluster ID")
                try:
                    cluster_id = self._nutter.dbclient.get_cluster_id_by_name(cluster_name)
                    logging.debug(f"Resolved cluster name '{cluster_name}' to cluster ID '{cluster_id}'")
                except ValueError as e:
                    self._logger.fatal(f"Error resolving cluster name: {e}")
                    exit(1)
            
            # Log execution parameters
            if serverless:
                logging.debug(f"Running tests with serverless compute (version: {serverless})")
            else:
                logging.debug(f"Running tests with cluster ID: {cluster_id}")
                
            logging.debug(""" Running tests. test_pattern: {} cluster_id: {} serverless: {} notebook_params: {} timeout: {}
                               junit_report: {} max_parallel_tests: {}
                               tags_report: {}  recursive:{} """
                          .format(test_pattern, cluster_id, serverless, timeout,
                                  junit_report, max_parallel_tests,
                                  tags_report, recursive, notebook_params))

            logging.debug(f"Executing test(s): {test_pattern}")

            if self._is_a_test_pattern(test_pattern):
                logging.debug('Executing pattern')
                results = self._nutter.run_tests(
                    test_pattern, cluster_id=cluster_id, timeout=timeout,
                    max_parallel_tests=max_parallel_tests, recursive=recursive, 
                    notebook_params=notebook_params, serverless=serverless)
                self._nutter.events_processor_wait()
                self._handle_results(results, junit_report, tags_report)
                return

            logging.debug('Executing single test')
            result = self._nutter.run_test(test_pattern, cluster_id=cluster_id, 
                                          timeout=timeout, notebook_params=notebook_params,
                                          serverless=serverless)

            self._handle_results([result], junit_report, tags_report)

        except Exception as error:
            self._logger.fatal(error)
            exit(1)

    def list(self, path, recursive=False):
        try:
            logging.debug(f"Running tests. path: {path}")
            results = self._nutter.list_tests(path, recursive)
            self._nutter.events_processor_wait()
            self._display_list_results(results)
        except Exception as error:
            self._logger.fatal(error)
            exit(1)

    def _handle_results(self, results, junit_report, tags_report):
        self._display_test_results(results)

        report_man = self._get_report_writer_manager(junit_report, tags_report)
        self._handle_reports(report_man, results)

        ExecutionResultsValidator().validate(results)

    @staticmethod
    def _get_report_writer_manager(junit_report, tags_report):
        writers = 0
        if junit_report:
            writers = ReportWriters.JUNIT
        if tags_report:
            writers = writers + ReportWriters.TAGS

        return reports.get_report_writer_manager(writers)

    @staticmethod
    def _handle_reports(report_manager, exec_results):
        if not report_manager.has_providers():
            logging.debug('No providers were registered.')
            return
        for provider in report_manager.providers_names():
            print(f'Writing {provider} report.')

        for exec_result in exec_results:
            t_result = api.to_test_results(
                exec_result.notebook_result.exit_output)
            if t_result is None:
                print('Warning:')
                print('\tThe output of {} is missing or the format is invalid.'.format(
                    exec_result.notebook_path))
                continue
            report_manager.add_result(exec_result.notebook_path, t_result)

        for file_name in report_manager.write():
            print('File {} written'.format(file_name))

    @staticmethod
    def _display_list_results(results):
        list_results_view = view.get_list_results_view(results)
        view.print_results_view(list_results_view)

    @staticmethod
    def _display_test_results(results):
        results_view = view.get_run_results_views(results)
        view.print_results_view(results_view)

    @staticmethod
    def _is_a_test_pattern(pattern):
        segments = pattern.split('/')
        if len(segments) > 0:
            search_pattern = segments[len(segments)-1]
            if api.TestNotebook._is_valid_test_name(search_pattern):
                return False
            return True
        logging.fatal(
            """ Invalid argument.
                 The value must be the full path to the test or a pattern """)

    @staticmethod
    def _print_cli_header():
        print(get_cli_header())

    def _set_nutter(self, debug):
        try:
            event_handler = ConsoleEventHandler(debug)
            self._nutter = api.get_nutter(event_handler)
        except (InvalidConfigurationException, ValueError) as ex:
            logging.debug(ex)
            self._print_config_error_and_exit()

    def _handle_show_version(self, version):
        if not version:
            return
        print(self._get_version_label())
        exit(0)

    @staticmethod
    def _get_version_label():
        version = get_nutter_version()
        return 'Nutter Version {}'.format(version)

    @staticmethod
    def _print_config_error_and_exit():
        print(""" Invalid configuration.\n
                  Set relevant environment variables: i.e., DATABRICKS_HOST and DATABRICKS_TOKEN
                  Example:
                  export DATABRICKS_HOST=<HOST>
                  export DATABRICKS_TOKEN=<TOKEN>
                  """)
        exit(1)

    @staticmethod
    def _set_debugging(debug, log_to_file):
        if debug:
            log_name = None
            if log_to_file:
                log_name = 'nutter-exec-{0:%Y.%m.%d.%H%M%S%f}.log'.format(
                    datetime.datetime.utcnow())
            logging.basicConfig(
                filename=log_name,
                format="%(asctime)s:%(levelname)s:%(message)s",
                level=logging.DEBUG)


def main():
    fire.Fire(NutterCLI)


if __name__ == '__main__':
    main()
