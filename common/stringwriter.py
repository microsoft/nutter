"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

class StringWriter():
    def __init__(self):
        self.result = ""

    def write(self, string_to_append):
        self.result += string_to_append

    def write_line(self, string_to_append):
        self.write(string_to_append + '\n')

    def to_string(self):
        return self.result
