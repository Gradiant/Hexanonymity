from enum import Enum
from typing import List, Set, Tuple

CoreData = Tuple[int, int, str, bool]

"""
* Data saved from every dot actling like a center of a group
* ``(core_index, core_index_precision, cell_in_overlap_with_most_free_indexes, agrupations_by_item_or_id)``
"""


class Indxs(Enum):
    FREE = 0
    CORE = 1
    __order__ = "FREE CORE"


class Ids(Enum):
    FREE = 0


class CellStats(dict):
    """
    * Stores the current state of a cell and allows special operations with them.
    * Includes abstraction to keep the car ids set of cell as small as possible with the lowerst computational effort
    """

    def __init__(self, soft_max_ids: int):
        super().__init__(((Indxs.FREE, []), (Indxs.CORE, []), (Ids.FREE, set())))
        self.__soft_max_ids = soft_max_ids

    def combine(self, o: "CellStats"):
        self[Indxs.FREE].extend(o[Indxs.FREE])
        self[Indxs.CORE].extend(o[Indxs.CORE])
        if len(self[Ids.FREE]) < self.__soft_max_ids:
            self[Ids.FREE].update(o[Ids.FREE])
        return self
