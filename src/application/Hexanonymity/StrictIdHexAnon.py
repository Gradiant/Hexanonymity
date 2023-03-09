from collections import defaultdict
from functools import reduce
import pandas as pd
import numpy as np
from sortedcontainers import SortedList, SortedSet
from h3 import geo_to_h3, k_ring, h3_to_parent
from src.application.Hexanonymity.H3Anonimyzer import H3Anonimyzer
from src.application.Hexanonymity.CellStats import CellStats, Indxs, Ids
from src.application.Hexanonymity.H3Anonimyzer import safe_dist

class StrictIdHexAnon(H3Anonimyzer):
    """
    * Hexanonimity but in case id-level protection is the maximum possible
    * Follows this stages:
            - Build groups from ``max_p`` to ``min_p`` with id_level protection
            - Build groups with ``min_p`` with loc_level protection
            - Group remaining locations in the same cell of ``min_p``
    """

    def __init__(self, k_anon: int, max_p: int = 14, min_p: int = 0):
        super().__init__(k_anon, max_p, min_p)

    def __str__(self) -> str:
        return "StrictIdHexanon"

    def __repr__(self) -> str:
        return "Hexanonimity"

    def apply(self, locs: pd.DataFrame, id_col: str, lat_col: str, lon_col: str, *critical_cols: str) -> pd.DataFrame:
        # --asserts and prepare data structures--
        anon_locs = locs.copy()
        mod_indexes = np.arange(len(anon_locs))
        id_col_indx, lat_col_indx, lon_col_indx = [anon_locs.columns.get_loc(c) for c in (id_col, lat_col, lon_col)]
        critical_cols_indxs = list({anon_locs.columns.get_loc(c) for c in critical_cols} | {lat_col_indx, lon_col_indx})
        k_anon, (min_p, max_p) = self.k_anon, self.p_bounds
        current_p = max_p + 1
        dot_level = False
        cells: dict[str, CellStats] = defaultdict(lambda: CellStats(k_anon))
        # --algorithm--
        # 1) Fill the cells data structure
        for i, row in enumerate(anon_locs.itertuples(index=False)):
            cell = cells[geo_to_h3(row[lat_col_indx], row[lon_col_indx], current_p)]
            cell[Indxs.FREE].append(i)
            cell[Ids.FREE].add(row[id_col_indx])
        # 2) Group elements lowering the precision each iteration
        while current_p > min_p:
            # 2.1 -> Analyze overlapping situations and build groups
            flower_overlaps: dict[str, SortedList[str]] = defaultdict(SortedList)
            for h3_id in cells.keys():
                for flower_cell_id in k_ring(h3_id, 1):
                    flower_overlaps[flower_cell_id].add(h3_id)
            for overlap in SortedSet(((*o,) for o in flower_overlaps.values() if len(o) > 1), key=len):
                # utility data structures
                most_free_indxs = max(overlap, key=lambda h3_id: len(cells[h3_id][Indxs.FREE]))
                combined = reduce(lambda curr, h3_id: curr.combine(cells[h3_id]), overlap, CellStats(k_anon))
                # cluster if possible
                core = None
                if len(combined[(Indxs if dot_level else Ids).FREE]) >= k_anon:
                    # create core with free's
                    chosen_cell = cells[most_free_indxs]
                    core = (chosen_cell[Indxs.FREE][0], current_p - 1, most_free_indxs)
                    chosen_cell[Indxs.CORE].append(core)
                elif combined[Indxs.FREE] and combined[Indxs.CORE]:
                    # attach free's to existing core
                    highst_core_p = max(combined[Indxs.CORE], key=lambda c: c[1])[1] + 1
                    core = min(combined[Indxs.CORE], key=lambda c: safe_dist(most_free_indxs, c[2], highst_core_p))
                if core is not None:
                    core_indx, *_ = core
                    mod_indexes[combined[Indxs.FREE]] = core_indx
                    for flower_center_id in overlap:
                        for opt in (Indxs, Ids):
                            cells[flower_center_id][opt.FREE].clear()
            # 2.2 -> Reduce precision and break if not more indexes
            if current_p == min_p + 1 and not dot_level:
                dot_level = True
            else:
                current_p -= 1
                free_indxs = False
                parent_cells = defaultdict(lambda: CellStats(k_anon))
                for h3_id, cell_stats in cells.items():
                    free_indxs = free_indxs or cell_stats[Indxs.FREE]
                    parent_cells[h3_to_parent(h3_id, current_p)].combine(cell_stats)
                if not free_indxs:
                    break
                cells = parent_cells
        # 3º) Add the outliers to the result
        for outliers_grp in (outs for s in cells.values() if (outs := s[Indxs.FREE])):
            mod_indexes[outliers_grp] = outliers_grp[0]
        # appy mods to the dataframe
        anon_locs.iloc[:, critical_cols_indxs] = anon_locs.iloc[mod_indexes, critical_cols_indxs].reset_index(drop=True)
        return anon_locs

    def apply_one_col(self, locs: pd.DataFrame, id_col: str, latlon_col: str, *critical_cols: str) -> pd.DataFrame:
        # --asserts and prepare data structures--
        anon_locs = locs.copy()
        mod_indexes = np.arange(len(anon_locs))
        id_col_indx, latlon_col_indx = [anon_locs.columns.get_loc(c) for c in (id_col, latlon_col)]
        critical_cols_indxs = list({anon_locs.columns.get_loc(c) for c in critical_cols} | {latlon_col_indx})
        k_anon, (min_p, max_p) = self.k_anon, self.p_bounds
        current_p = max_p + 1
        dot_level = False
        cells: dict[str, CellStats] = defaultdict(lambda: CellStats(k_anon))
        # --algorithm--
        # 1) Fill the cells data structure
        for i, row in enumerate(anon_locs.itertuples(index=False)):
            latlon = row[latlon_col_indx]
            if type(latlon) == str:
                latlon = latlon.strip().split(",")
            lat, lon = map(float, latlon)

            cell = cells[geo_to_h3(lat, lon, current_p)]
            cell[Indxs.FREE].append(i)
            cell[Ids.FREE].add(row[id_col_indx])
        # 2) Group elements lowering the precision each iteration
        while current_p > min_p:
            # 2.1 -> Analyze overlapping situations and build groups
            flower_overlaps: dict[str, SortedList[str]] = defaultdict(SortedList)
            for h3_id in cells.keys():
                for flower_cell_id in k_ring(h3_id, 1):
                    flower_overlaps[flower_cell_id].add(h3_id)
            for overlap in SortedSet(((*o,) for o in flower_overlaps.values() if len(o) > 1), key=len):
                # utility data structures
                most_free_indxs = max(overlap, key=lambda h3_id: len(cells[h3_id][Indxs.FREE]))
                combined = reduce(lambda curr, h3_id: curr.combine(cells[h3_id]), overlap, CellStats(k_anon))
                # cluster if possible
                core = None
                if len(combined[(Indxs if dot_level else Ids).FREE]) >= k_anon:
                    # create core with free's
                    chosen_cell = cells[most_free_indxs]
                    core = (chosen_cell[Indxs.FREE][0], current_p - 1, most_free_indxs)
                    chosen_cell[Indxs.CORE].append(core)
                elif combined[Indxs.FREE] and combined[Indxs.CORE]:
                    # attach free's to existing core
                    highst_core_p = max(combined[Indxs.CORE], key=lambda c: c[1])[1] + 1
                    core = min(combined[Indxs.CORE], key=lambda c: safe_dist(most_free_indxs, c[2], highst_core_p))
                if core is not None:
                    core_indx, *_ = core
                    mod_indexes[combined[Indxs.FREE]] = core_indx
                    for flower_center_id in overlap:
                        for opt in (Indxs, Ids):
                            cells[flower_center_id][opt.FREE].clear()
            # 2.2 -> Reduce precision and break if not more indexes
            if current_p == min_p + 1 and not dot_level:
                dot_level = True
            else:
                current_p -= 1
                free_indxs = False
                parent_cells = defaultdict(lambda: CellStats(k_anon))
                for h3_id, cell_stats in cells.items():
                    free_indxs = free_indxs or cell_stats[Indxs.FREE]
                    parent_cells[h3_to_parent(h3_id, current_p)].combine(cell_stats)
                if not free_indxs:
                    break
                cells = parent_cells
        # 3º) Add the outliers to the result
        for outliers_grp in (outs for s in cells.values() if (outs := s[Indxs.FREE])):
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
        k_anon, (min_p, max_p) = self.k_anon, self.p_bounds
        current_p = max_p + 1
        dot_level = False
        cells: dict[str, CellStats] = defaultdict(lambda: CellStats(k_anon))
        # --algorithm--
        # 1) Fill the cells data structure
        for i, row in enumerate(anon_locs.itertuples(index=False)):
            cell = cells[geo_to_h3(row[col("lat1")], row[col("lon1")], current_p)]
            cell[Indxs.FREE].append(i)
            cell[Ids.FREE].add(row[col("id")])
        # 2) Group elements lowering the precision each iteration
        while current_p > min_p:
            # 2.1 -> Analyze overlapping situations and build groups
            flower_overlaps: dict[str, SortedList[str]] = defaultdict(SortedList)
            for h3_id in cells.keys():
                for flower_cell_id in k_ring(h3_id, 1):
                    flower_overlaps[flower_cell_id].add(h3_id)
            for overlap in SortedSet(((*o,) for o in flower_overlaps.values() if len(o) > 1), key=len):
                # utility data structures
                most_free_indxs = max(overlap, key=lambda h3_id: len(cells[h3_id][Indxs.FREE]))
                combined = reduce(lambda curr, h3_id: curr.combine(cells[h3_id]), overlap, CellStats(k_anon))
                # cluster if possible
                core = None
                if len(combined[(Indxs if dot_level else Ids).FREE]) >= k_anon:
                    # create core with free's
                    chosen_cell = cells[most_free_indxs]
                    core = (chosen_cell[Indxs.FREE][0], current_p - 1, most_free_indxs, dot_level)
                    chosen_cell[Indxs.CORE].append(core)
                elif combined[Indxs.FREE] and combined[Indxs.CORE]:
                    # attach free's to existing core
                    highst_core_p = max(combined[Indxs.CORE], key=lambda core: core[1])[1] + 1
                    core = min(combined[Indxs.CORE], key=lambda c: safe_dist(most_free_indxs, c[2], highst_core_p))
                if core is not None:
                    core_indx, core_p, _, core_dot_level = core
                    mod_loc_indxs[combined[Indxs.FREE]] = core_indx
                    prec_vals[combined[Indxs.FREE]] = (core_p, current_p - 1)
                    safe_vals[combined[Indxs.FREE]] = (0, 1, 0) if core_dot_level else (1, 0, 0)
                    for flower_center_id in overlap:
                        for opt in (Indxs, Ids):
                            cells[flower_center_id][opt.FREE].clear()
            # 2.2 -> Reduce precision and break if not more indexes
            if current_p == min_p + 1 and not dot_level:
                dot_level = True
            else:
                current_p -= 1
                free_indxs = False
                parent_cells: dict[str, CellStats] = defaultdict(lambda: CellStats(k_anon))
                for h3_id, cell_stats in cells.items():
                    free_indxs = free_indxs or cell_stats[Indxs.FREE]
                    parent_cells[h3_to_parent(h3_id, current_p)].combine(cell_stats)
                if not free_indxs:
                    break
                cells = parent_cells
        # 3º) Add the outliers to the result
        for outliers_grp in (outs for s in cells.values() if (outs := s[Indxs.FREE])):
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
