from typing import List, Dict, Union
from pydantic import BaseModel, validator

class OperationConfiguration(BaseModel):
    type: str
    params: Dict
    field: Union[List[str], str]
    working_point: int


    def __eq__(self, other):
        if isinstance(other, OperationConfiguration):
            return all(
                [
                    self.type == other.type,
                    self.params == other.params,
                    self.field == other.field,
                    self.working_point == other.working_point,
                ]
            )
        return False

    def __hash__(self):
        return hash(self.json())
