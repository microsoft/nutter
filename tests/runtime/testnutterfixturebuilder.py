"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

from runtime.nutterfixture import NutterFixture

class TestNutterFixtureBuilder():
    def __init__(self):
        self.attributes = {}
        self.class_name = "ImplementingClass"

    def with_name(self, class_name):
        self.class_name = class_name
        return self

    def with_before_all(self, func = lambda self: 1 == 1):
        self.attributes.update({"before_all" : func })
        return self

    def with_before(self, test_name, func = lambda self: 1 == 1):
        full_test_name = "before_" + test_name
        self.attributes.update({full_test_name : func})
        return self

    def with_assertion(self, test_name, func = lambda self: 1 == 1):
        full_test_name = "assertion_" + test_name
        self.attributes.update({full_test_name : func})
        return self

    def with_run(self, test_name, func = lambda self: 1 == 1):
        full_test_name = "run_" + test_name
        self.attributes.update({full_test_name : func})
        return self

    def with_after(self, test_name, func = lambda self: 1 == 1):
        full_test_name = "after_" + test_name
        self.attributes.update({full_test_name : func})
        return self

    def with_after_all(self, func = lambda self: 1 == 1):
        self.attributes.update({"after_all" : func })
        return self
        
    def with_test(self, test_name, func = lambda self: 1 == 1):
        full_test_name = test_name
        self.attributes.update({full_test_name : func})
        return self

    def build(self):
        new_class = type(self.class_name, (NutterFixture,), self.attributes)
        return new_class  
