"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

from abc import abstractmethod, ABCMeta


class SerializableData:
    __metaclass__ = ABCMeta

    @abstractmethod
    def serialize(self):
        pass

    @abstractmethod
    def deserialize(self, pickle_string):
        pass
