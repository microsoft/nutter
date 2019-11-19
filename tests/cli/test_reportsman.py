"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

import pytest
from common.testresult import TestResults, TestResult
from common.resultreports import JunitXMLReportWriter
from common.resultreports import TagsReportWriter
from cli.reportsman import ReportWriterManager, ReportWriters, ReportWritersTypes
import common.api as nutter_api

def test__reportwritermanager_ctor__junit_report__valid_manager():
    report_writer_man = ReportWriterManager(ReportWriters.JUNIT)

    assert len(report_writer_man._providers) == 1
    report_man = report_writer_man._providers[ReportWritersTypes.JUNIT]
    assert isinstance(report_man, JunitXMLReportWriter)

def test__reportwritermanager_ctor__tags_report__valid_manager():
    report_writer_man = ReportWriterManager(ReportWriters.TAGS)

    assert len(report_writer_man._providers) == 1
    report_man = report_writer_man._providers[ReportWritersTypes.TAGS]
    assert isinstance(report_man, TagsReportWriter)


def test__reportwritermanager_ctor__tags_and_junit_report__valid_manager():
    report_writer_man = ReportWriterManager(ReportWriters.TAGS + ReportWriters.JUNIT)

    assert len(report_writer_man._providers) == 2
    report_man = report_writer_man._providers[ReportWritersTypes.TAGS]
    assert isinstance(report_man, TagsReportWriter)
    report_man = report_writer_man._providers[ReportWritersTypes.JUNIT]
    assert isinstance(report_man, JunitXMLReportWriter)


def test__reportwritermanager_ctor__invalid_report__empty_manager():
    report_writer_man = ReportWriterManager(0)

    assert len(report_writer_man._providers) == 0

def test__add_result__junit_provider_one_test_result__provider_has_data():
    report_writer_man = ReportWriterManager(ReportWriters.JUNIT)
    test_results = TestResults()
    test_results.append(TestResult("mycase", True, 10, []))
    report_writer_man.add_result('notepad', test_results)

    report_man = report_writer_man._providers[ReportWritersTypes.JUNIT]
    assert isinstance(report_man, JunitXMLReportWriter)
    assert report_man.has_data()


def test__add_result__junit_provider_zero_test_result__provider_has_data():
    report_writer_man = ReportWriterManager(ReportWriters.JUNIT)
    test_results = TestResults()
    report_writer_man.add_result('notepad', test_results)

    report_man = report_writer_man._providers[ReportWritersTypes.JUNIT]
    assert report_man.has_data()

def test__add_result__tags_provider_one_test_result__provider_has_data():
    report_writer_man = ReportWriterManager(ReportWriters.TAGS)
    test_results = TestResults()
    test_results.append(TestResult("mycase", True, 10, ['hello']))
    report_writer_man.add_result('notepad', test_results)

    report_man = report_writer_man._providers[ReportWritersTypes.TAGS]
    assert report_man.has_data()


def test__write__two_providers__returns_two_names():
    report_writer_man = ReportWriterManager(ReportWriters.TAGS + ReportWriters.JUNIT)
    test_results = TestResults()
    test_results.append(TestResult("mycase", True, 10, ['hello']))
    report_writer_man.add_result('notepad', test_results)

    results = report_writer_man.providers_names()

    assert len(results) == 2
