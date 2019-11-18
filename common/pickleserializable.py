from abc import abstractmethod, ABCMeta

class PickleSerializable():
    __metaclass__ = ABCMeta

    @abstractmethod
    def serialize(self):
        pass

    @abstractmethod
    def deserialize(self):
        pass