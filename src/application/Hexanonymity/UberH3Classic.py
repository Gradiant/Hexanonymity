from collections import defaultdict
from typing import Dict
import pandas as pd
import numpy as np
from h3 import geo_to_h3, h3_to_parent
from src.application.Hexanonymity.CellStats import CellStats
from src.application.Hexanonymity.H3Anonimyzer import H3Anonimyzer

class UberH3Classic(H3Anonimyzer):
    """
    * Like adaptative interval cloaking but from down to up
    * Doesn't use the overlapping mechanism
    * Follows this stages:
            - Build groups from ``max_p`` to ``min_p`` with id_level protection
            - Build groups with ``min_p`` with loc_level protection
            - Group remaining locations in the same cell of ``min_p``
    """

    def __init__(self, k_anon: int, max_p: int = 14, min_p: int = 0):
        super().__init__(k_anon, max_p, min_p)

    def __str__(self) -> str:
        return "UberH3Classic-" + super().__str__()

    def __repr__(self) -> str:
        return "UberH3 Classic"

    def apply(self, locs: pd.DataFrame, id_col: str, lat_col: str, lon_col: str, *critical_cols: str) -> pd.DataFrame:
        # --asserts and prepare data structures--
        anon_locs = locs.copy()
        mod_indexes = np.arange(len(anon_locs))
        id_col_indx, lat_col_indx, lon_col_indx = [anon_locs.columns.get_loc(c) for c in (id_col, lat_col, lon_col)]
        critical_cols_indxs = list({anon_locs.columns.get_loc(c) for c in critical_cols} | {lat_col_indx, lon_col_indx})
        k_anon, (min_p, max_p) = self.k_anon, self.p_bounds
        current_p = max_p + 1
        dot_level = False
        cells: Dict[str, CellStats] = defaultdict(lambda: CellStats(k_anon))
        # --algorithm--
        # 1) Fill the cells data structure
        for i, row in enumerate(anon_locs.itertuples(index=False)):
            cell = cells[geo_to_h3(row[lat_col_indx], row[lon_col_indx], current_p)]
            cell.free_indxs.append(i)
            cell.free_ids.add(row[id_col_indx])
        # 2) Group elements lowering the precision each iteration
        while current_p > min_p:
            for cell in cells.values():
                core = None
                if len(cell.free_indxs if dot_level else cell.free_ids) >= k_anon:
                    # group can be built with all new members
                    core = cell.free_indxs[0]
                    cell.core_data.append(core)
                elif cell.free_indxs and cell.core_data:
                    # group can be built by attaching to one previously built
                    core = cell.core_data[0]
                if core is not None:
                    mod_indexes[cell.free_indxs] = core
                    cell.clear_free()
            if current_p == min_p and not dot_level:
                dot_level = True
            else:
                current_p -= 1
                free_indxs = False
                parent_cells = defaultdict(lambda: CellStats(k_anon))
                for h3_id, cell_stats in cells.items():
                    free_indxs = free_indxs or cell_stats.free_indxs
                    parent_cells[h3_to_parent(h3_id, current_p)].combine(cell_stats)
                if not free_indxs:
                    break
                cells = parent_cells
        # 3º) Add the outliers to the result
        for outliers_grp in (outs for s in cells.values() if (outs := s.free_indxs)):
            mod_indexes[outliers_grp] = outliers_grp[0]
        # appy mods to the dataframe
        anon_locs.iloc[:, critical_cols_indxs] = anon_locs.iloc[mod_indexes, critical_cols_indxs].reset_index(drop=True)

    def apply_debug(self, locs: pd.DataFrame, id_col: str, lat_col: str, lon_col: str, time_col: str) -> pd.DataFrame:
        # --asserts and prepare data structures--
        assert isinstance(locs, pd.DataFrame)
        anon_locs = locs[[id_col, time_col, lat_col, lon_col]].copy()
        # change column names
        anon_locs.columns = ["id", "time", "lat1", "lon1"]
        anon_locs = anon_locs.assign(
            lat2=np.nan, lon2=np.nan, center_p=np.nan, line_p=np.nan, id_safe=np.nan, loc_safe=np.nan, unsafe=np.nan
        )
        col = anon_locs.columns.get_loc
        mod_loc_indxs = np.arange(len(anon_locs))
        prec_vals = np.array([(0, 0) for _ in range(len(anon_locs))])
        safe_vals = np.array([(0, 0, 0) for _ in range(len(anon_locs))])
        k_anon, (min_p, max_p) = self.k_anon, self.p_bounds
        current_p = max_p
        dot_level, outliers = False, False
        cells: dict[str, CellStats] = defaultdict(lambda: CellStats(k_anon))
        # --algorithm--
        # 1) Fill the cells data structure
        for i, row in enumerate(anon_locs.itertuples(index=False)):
            cell = cells[geo_to_h3(row[col("lat1")], row[col("lon1")], current_p)]
            cell.free_indxs.append(i)
            cell.free_ids.add(row[col("id")])
        # 2) Group elements lowering the precision each iteration
        while current_p >= min_p:
            for cell in cells.values():
                if outliers and (outs := cell.free_indxs):
                    mod_loc_indxs[outs] = outs[0]
                    prec_vals[outs] = (current_p, current_p)
                    safe_vals[outs] = (0, 0, 1)
                else:
                    core = None
                    if len(cell.free_indxs if dot_level else cell.free_ids) >= k_anon:
                        # group can be built with all new members
                        core: CellStats.CoreData = (cell.free_indxs[0], current_p, dot_level)
                        cell.core_data.append(core)
                    elif cell.free_indxs and cell.core_data:
                        core = cell.core_data[0]
                    if core is not None:
                        core_indx, core_p, core_dot_level = core
                        mod_loc_indxs[cell.free_indxs] = core_indx
                        prec_vals[cell.free_indxs] = (core_p, current_p)
                        safe_vals[cell.free_indxs] = (0, 1, 0) if core_dot_level else (1, 0, 0)
                        cell.clear_free()
            if current_p == min_p and not dot_level:
                dot_level = True
            elif current_p == min_p and dot_level and not outliers:
                outliers = True
            else:
                current_p -= 1
                free_indxs = False
                parent_cells: dict[str, CellStats] = defaultdict(lambda: CellStats(k_anon))
                for h3_id, cell_stats in cells.items():
                    free_indxs = free_indxs or cell_stats.free_indxs
                    parent_cells[h3_to_parent(h3_id, current_p)].combine(cell_stats)
                if not free_indxs:
                    break
                cells = parent_cells
        # 4º) Apply mods to dataframe and return the result
        anon_locs.iloc[:, [col(l) for l in ("lat2", "lon2")]] = anon_locs.iloc[
            mod_loc_indxs, [col(l) for l in ("lat1", "lon1")]
        ].reset_index(drop=True)
        anon_locs.loc[:, ["center_p", "line_p"]] = prec_vals
        anon_locs.loc[:, ["id_safe", "loc_safe", "unsafe"]] = safe_vals
        return anon_locs
