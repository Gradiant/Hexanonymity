from abc import abstractmethod
from src.domain.operations.operation_configuration import OperationConfiguration
from pandas import DataFrame

class IOperation:
    @property
    def configuration(self) -> OperationConfiguration:
        raise NotImplementedError()

    @abstractmethod
    def apply(self, data: DataFrame) -> DataFrame:
        raise NotImplementedError()

    def __eq__(self, other):
        if isinstance(other, IOperation):
            return self.configuration == other.configuration
        return False

    def __hash__(self):
        return hash(self.configuration)
