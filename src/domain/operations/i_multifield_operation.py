from abc import abstractmethod


class IMultifieldOperation:
    @abstractmethod
    def get_multifield(self):
        raise NotImplementedError()
