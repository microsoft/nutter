"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

import pytest
from common.testresult import TestResults, TestResult
from common.resultreports import JunitXMLReportWriter
from common.resultreports import TagsReportWriter

def test_junitxmlreportwriter_add_result__invalid_params__raises_valueerror():
    writer = JunitXMLReportWriter()

    with pytest.raises(ValueError):
        writer.add_result(None, None)


def test_tagsreportwriter_add_result__invalid_params__raises_valueerror():
    writer = TagsReportWriter()

    with pytest.raises(ValueError):
        writer.add_result(None, None)


def test_tagsreportwriter_add_result__1_test_result__1_valid_row():
    writer = TagsReportWriter()
    test_results = TestResults()
    test_name = 'case1'
    duration = 10
    tags = ['hello', 'hello']
    test_result = TestResult(test_name, True, duration, tags)
    test_results.append(test_result)
    notebook_name = 'test_mynotebook'

    writer.add_result(notebook_name, test_results)

    assert len(writer._rows) == 1
    row = writer._rows[0]

    assert row.notebook_name == notebook_name
    assert row.test_name == test_name
    assert row.passed_str == 'PASSED'
    assert row.duration == duration
    assert row.tags == row._to_tag_string(tags)
