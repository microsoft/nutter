"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

import common.api as nutter_api
from enum import Enum
from enum import IntEnum

import logging


def get_report_writer_manager(writers):
    return ReportWriterManager(writers)


class ReportWriterManager(object):

    def __init__(self, report_writers):
        self._set_providers(report_writers)
        super().__init__()

    def _set_providers(self, report_writers):
        self._providers = {}
        logging.debug(
            'Setting the following report writers: {}'.format(report_writers))

        if ReportWriters.JUNIT & report_writers:
            writer = nutter_api.get_report_writer(
                ReportWritersTypes.JUNIT.value)
            self._providers[ReportWritersTypes.JUNIT] = writer

        if ReportWriters.TAGS & report_writers:
            writer = nutter_api.get_report_writer(
                ReportWritersTypes.TAGS.value)
            self._providers[ReportWritersTypes.TAGS] = writer

    def add_result(self, notebook_path, testresult):
        for key, provider in self._providers.items():
            logging.debug('Adding a test result to {} providers.'.format(key))
            provider.add_result(notebook_path, testresult)

    def write(self):
        file_names = []
        for key, provider in self._providers.items():
            if not provider.has_data():
                logging.debug('No test results to write for {}.'.format(key))
                continue
            file_name = provider.write()
            file_names.append(file_name)
        return file_names

    def providers_names(self):
        return [key for key, value in self._providers.items()]

    def has_providers(self):
        return len(self._providers) > 0


class ReportWritersTypes(Enum):
    JUNIT = 'JunitXMLReportWriter'
    TAGS = 'TagsReportWriter'


class ReportWriters(IntEnum):
    JUNIT = 1
    TAGS = 2
