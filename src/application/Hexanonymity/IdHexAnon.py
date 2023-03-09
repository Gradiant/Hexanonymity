from collections import defaultdict
from typing import Optional
import pandas as pd
import numpy as np
from sortedcontainers import SortedList, SortedSet
from h3 import geo_to_h3, k_ring, h3_to_parent
from src.application.Hexanonymity.CellStats import CellStats, CoreData
from src.application.Hexanonymity.H3Anonimyzer import H3Anonimyzer, safe_dist


class IdHexAnon(H3Anonimyzer):
    """
    * Anonimyzes locations using the hexanonimity approach
    * Has an aditional parameter `k-break-p` to switch from *id-level* to **loc-level** clustering
    * By default
    * Assumes K-anonimity at location's id level NOT locations instance level
    * Guarantees K-anonimity at a certain precision level and geo-indistiguishability out of this bound
    * Assumes the existence of a *break point* in between precission bounds providing this behaviour:
            - From ``max_p`` until ``break_p`` (not included) anonimyzes by id -> k-anonimity
            - From ``break_p`` until ``min_p`` anonimyzes by location -> geo-indistinguishability
            - Remaining free locations beyond min_p -> geo-indistinguishability not ensured (outliers)
    """

    @property
    def k_break_p(self):
        """
        * Uber H3 precision where switch from id-level anonimization to loc-level
        * By default the minimum precision level
        """
        return self.__k_break_p - 1

    @k_break_p.setter
    def k_break_p(self, k_break_p: int):
        min_p, max_p = self.p_bounds
        assert k_break_p in range(min_p, max_p + 1)
        self.__k_break_p = k_break_p + 1

    @k_break_p.deleter
    def k_break_p(self):
        raise AttributeError("Cannot delete k-break-p")

    def __init__(self, k_anon: int, max_p: int = 14, min_p: int = 0, k_break_p: Optional[int] = None):
        super().__init__(k_anon, max_p, min_p)
        self.k_break_p = k_break_p or min_p

    def __str__(self) -> str:
        min_p, _ = self.p_bounds
        return f"IdHex-{super()}" + f"-break{self.k_break_p}" * (self.k_break_p != min_p)

    def apply(self, locs: pd.DataFrame, id_col: str, lat_col: str, lon_col: str, *critical_cols: str) -> pd.DataFrame:
        # --asserts and prepare data structures--
        anon_locs = locs.copy()
        mod_indexes = np.arange(len(anon_locs))
        id_col_indx, lat_col_indx, lon_col_indx = [anon_locs.columns.get_loc(c) for c in (id_col, lat_col, lon_col)]
        critical_cols_indxs = list({anon_locs.columns.get_loc(c) for c in critical_cols} | {lat_col_indx, lon_col_indx})
        k_anon, (min_p, max_p), k_break_p = self.k_anon, self.p_bounds, self.k_break_p + 1
        current_p = max_p + 1
        cells: dict[str, CellStats] = defaultdict(lambda: CellStats(k_anon))
        # --algorithm--
        # 1) Fill the cells data structure
        for i, row in enumerate(anon_locs.itertuples(index=False)):
            cell = cells[geo_to_h3(row[lat_col_indx], row[lon_col_indx], current_p)]
            cell.free_indxs.append(i)
            cell.free_ids.add(row[id_col_indx])
        # 2) Group elements lowering the precision each iteration
        while current_p > min_p:
            dot_level = k_break_p >= current_p
            # 2.1 -> Analyze overlapping situations and build groups
            flower_overlaps: dict[str, SortedList[str]] = defaultdict(SortedList)
            for h3_id in cells.keys():
                for flower_cell_id in k_ring(h3_id, 1):
                    flower_overlaps[flower_cell_id].add(h3_id)
            for overlap in SortedSet(((*o,) for o in flower_overlaps.values() if len(o) > 1), key=len):
                # utility data structures
                most_free_indxs = max(overlap, key=lambda h3_id: len(cells[h3_id].free_indxs))
                combined = sum(map(lambda h3_id: cells[h3_id], overlap), start=CellStats(k_anon))
                # cluster if possible
                core = None
                if len(combined.free_indxs if dot_level else combined.free_ids) >= k_anon:
                    # create core with free's
                    chosen_cell = cells[most_free_indxs]
                    core = (chosen_cell.free_indxs[0], current_p - 1, most_free_indxs)
                    chosen_cell.core_data.append(core)
                elif combined.free_indxs and combined.core_data:
                    # attach free's to existing core
                    highst_core_p = max(combined.core_data, key=lambda c: c[1])[1] + 1
                    core = min(combined.core_data, key=lambda c: safe_dist(most_free_indxs, c[2], highst_core_p))
                if core is not None:
                    core_indx, *_ = core
                    mod_indexes[combined.free_indxs] = core_indx
                    for flower_center_id in overlap:
                        cells[flower_center_id].clear_free()
            # 2.2 -> Reduce precision and break if not more indexes
            current_p -= 1
            free_indxs = False
            parent_cells = defaultdict(lambda: CellStats(k_anon))
            for h3_id, cell_stats in cells.items():
                free_indxs = free_indxs or cell_stats.free_indxs
                parent_cells[h3_to_parent(h3_id, current_p)] += cell_stats
            if not free_indxs:
                break
            cells = parent_cells
        # 3º) Add the outliers to the result
        for outliers_grp in (outs for s in cells.values() if (outs := s.free_indxs)):
            mod_indexes[outliers_grp] = outliers_grp[0]
        # appy mods to the dataframe
        anon_locs.iloc[:, critical_cols_indxs] = anon_locs.iloc[mod_indexes, critical_cols_indxs].reset_index(drop=True)
        return anon_locs

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
        k_anon, (min_p, max_p), k_break_p = self.k_anon, self.p_bounds, self.k_break_p + 1
        current_p = max_p + 1
        cells: dict[str, CellStats] = defaultdict(lambda: CellStats(k_anon))
        # --algorithm--
        # 1) Fill the cells data structure
        for i, row in enumerate(anon_locs.itertuples(index=False)):
            cell = cells[geo_to_h3(row[col("lat1")], row[col("lon1")], current_p)]
            cell.free_indxs.append(i)
            cell.free_ids.add(row[col("id")])
        # 2) Group elements lowering the precision each iteration
        while current_p > min_p:
            dot_level = k_break_p >= current_p
            # 2.1 -> Analyze overlapping situations and build groups
            flower_overlaps: dict[str, SortedList[str]] = defaultdict(SortedList)
            for h3_id in cells.keys():
                for flower_cell_id in k_ring(h3_id, 1):
                    flower_overlaps[flower_cell_id].add(h3_id)
            for overlap in SortedSet(((*o,) for o in flower_overlaps.values() if len(o) > 1), key=len):
                # utility data structures
                most_free_indxs = max(overlap, key=lambda h3_id: len(cells[h3_id].free_indxs))
                combined = sum(map(lambda h3_id: cells[h3_id], overlap), start=CellStats(k_anon))
                # cluster if possible
                core = None
                if len(combined.free_indxs if dot_level else combined.free_ids) >= k_anon:
                    # create core with free's
                    chosen_cell = cells[most_free_indxs]
                    core: CoreData = (chosen_cell.free_indxs[0], current_p - 1, most_free_indxs)
                    chosen_cell.core_data.append(core)
                elif combined.free_indxs and combined.core_data:
                    # attach free's to existing core
                    highst_core_p = max(combined.core_data, key=lambda c: c[1])[1] + 1
                    core = min(combined.core_data, key=lambda c: safe_dist(most_free_indxs, c[2], highst_core_p))
                if core is not None:
                    core_indx, core_p, *_ = core
                    mod_loc_indxs[combined.free_indxs] = core_indx
                    prec_vals[combined.free_indxs] = (core_p, current_p - 1)
                    safe_vals[combined.free_indxs] = (1, 0, 0) if core_p + 1 > k_break_p else (0, 1, 0)
                    for flower_center_id in overlap:
                        cells[flower_center_id].clear_free()
            # 2.2 -> Reduce precision and break if not more indexes
            current_p -= 1
            free_indxs = False
            parent_cells: dict[str, CellStats] = defaultdict(lambda: CellStats(k_anon))
            for h3_id, cell_stats in cells.items():
                free_indxs = free_indxs or cell_stats.free_indxs
                parent_cells[h3_to_parent(h3_id, current_p)] += cell_stats
            if not free_indxs:
                break
            cells = parent_cells
        # 3º) Add the outliers to the result
        for outliers_grp in (outs for s in cells.values() if (outs := s.free_indxs)):
            mod_loc_indxs[outliers_grp] = outliers_grp[0]
            prec_vals[outliers_grp] = (current_p, current_p)
            safe_vals[outliers_grp] = (0, 0, 1)
        # 4º) Apply mods to dataframe and return the result
        anon_locs.iloc[:, [col(l) for l in ("lat2", "lon2")]] = anon_locs.iloc[
            mod_loc_indxs, [col(l) for l in ("lat1", "lon1")]
        ].reset_index(drop=True)
        anon_locs.loc[:, ["center_p", "line_p"]] = prec_vals
        anon_locs.loc[:, ["id_safe", "loc_safe", "unsafe"]] = safe_vals
        return anon_locs
