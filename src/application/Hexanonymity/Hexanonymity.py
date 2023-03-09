from typing import List, Dict, Optional
from pandas import DataFrame
from src.application.Hexanonymity.StrictIdHexAnon import StrictIdHexAnon
from src.domain.operations.i_multifield_operation import IMultifieldOperation
from src.domain.operations.ioperation import IOperation
from src.domain.operations.operation_configuration import OperationConfiguration


class Hexanonimity(IOperation, IMultifieldOperation):
    def __init__(
        self,
        fields: List[str],
        id_col: str,
        sensitive_cols: Optional[List[str]],
        configuration: Dict[str, int],
        working_point=0,
    ):
        self._configuration = configuration
        self.id_col = id_col
        self.sensitive_cols = sensitive_cols
        self.fields = fields
        self.working_point = working_point

        self.k = None
        self.min_p = None
        self.max_p = None

    def get_multifield(self):
        multifields = self.fields
        if self.id_col:
            multifields.append(self.id_col)
        if self.sensitive_cols:
            multifields += self.sensitive_cols
        return multifields

    @property
    def configuration(self):
        params = {
            "id_col": self.id_col,
            "sensitive_cols": self.sensitive_cols,
            "values": self._configuration,
        }  # k, min_p, max_p
        return OperationConfiguration(
            type="HEXANONIMITY",
            field=self.fields,
            params=params,
            working_point=self.working_point,
        )

    def apply(self, data: DataFrame) -> DataFrame:
        if "k" in self._configuration:
            self.k = int(self._configuration["k"])
            if self.k < 1:
                raise ValueError("K must be 1 or greater")
        else:
            self.k = 2

        if "min_p" in self._configuration:
            self.min_p = int(self._configuration["min_p"])
            if not 0 <= self.min_p <= 14:
                raise ValueError("min_p must be from 0 to 14")
        else:
            self.min_p = 0

        if "max_p" in self._configuration:
            self.max_p = int(self._configuration["max_p"])
            if not 0 <= self.max_p <= 14:
                raise ValueError("max_p must be from 0 to 14")
        else:
            self.max_p = 14

        hexa_anonymizer = StrictIdHexAnon(
            k_anon=self.k, max_p=self.max_p, min_p=self.min_p
        )
        return hexa_anonymizer.apply_one_col(
            data, self.id_col, self.fields[0], *self.sensitive_cols
        )
