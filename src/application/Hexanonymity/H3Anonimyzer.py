from typing import Tuple
from h3 import h3_to_center_child, h3_distance
from src.application.Hexanonymity.KAnonimyzer import KAnonimyzer

def safe_dist(id1: str, id2: str, res: int) -> int:
    """
    * Calculates the distance between two h3-cells given the resolution of the path between them
    * Support comparaisons between different cell precisions unlike the api
    * No time complexity added
    * The ``res`` must be the **highest** possible precision of the cells being compared
            * The possible corrections will increase precision until reach `res`
    """
    if id1 == id2:
        return 0
    id1, id2 = map(lambda id: h3_to_center_child(id, res), (id1, id2))
    return h3_distance(id1, id2)


class H3Anonimyzer(KAnonimyzer):
    """
    * Class from which all implementations of anonimyzers using Uber H3 derives
    * Defines an attribute representing the maximum and minimum levels in the index hierarchy used as bounds
    * Also includes utility methods to operate with the library
    """

    @property
    def p_bounds(self) -> Tuple[int, int]:
        """
        * Return the precision bounds of the analysis
        * Shape as a tuple ``(min_p,max_p)``
        * ``max_p`` bigger or equal than ``min_p``
        * 16 precisions from 0 to 15 -> https://h3geo.org/docs/core-library/restable
        * Precision level nº15 is reserved so valid precision levels are [0, 14]
        """
        return (self.__min_p, self.__max_p)

    @p_bounds.setter
    def p_bounds(self, p_bounds: Tuple[int, int]) -> None:
        assert all(p in range(15) for p in p_bounds)
        min_p, max_p = p_bounds
        assert max_p >= min_p
        self.__min_p = min_p
        self.__max_p = max_p

    def __init__(self, k_anon: int, max_p: int, min_p: int):
        super().__init__(k_anon)
        self.p_bounds = (min_p, max_p)

    def __str__(self) -> str:
        min_p, max_p = self.p_bounds
        return f"{super()!s}-p[{max_p},{min_p}]"

    @property
    def kepler_config(self) -> dict:
        return {
            "version": "v1",
            "config": {
                "visState": {
                    "filters": [
                        {
                            "dataId": ["h3_levels"],
                            "id": "4f1r8uoo8",
                            "name": ["hex_p"],
                            "type": "range",
                            "value": [10, 13],
                            "enlarged": False,
                            "plotType": "histogram",
                            "animationWindow": "free",
                            "yAxis": None,
                            "speed": 1,
                        },
                        {
                            "dataId": ["anon_locs"],
                            "id": "unahvxar",
                            "name": ["time"],
                            "type": "timeRange",
                            "value": [1642750410000, 1642751400000],
                            "enlarged": False,
                            "plotType": "histogram",
                            "animationWindow": "free",
                            "yAxis": None,
                            "speed": 1,
                        },
                        {
                            "dataId": ["anon_locs"],
                            "id": "h3vtfo90p",
                            "name": ["unsafe"],
                            "type": "range",
                            "value": [0, 1],
                            "enlarged": False,
                            "plotType": "histogram",
                            "animationWindow": "free",
                            "yAxis": None,
                            "speed": 1,
                        },
                        {
                            "dataId": ["anon_locs"],
                            "id": "0ypp396i",
                            "name": ["loc_safe"],
                            "type": "range",
                            "value": [0, 1],
                            "enlarged": False,
                            "plotType": "histogram",
                            "animationWindow": "free",
                            "yAxis": None,
                            "speed": 1,
                        },
                        {
                            "dataId": ["anon_locs"],
                            "id": "zjj7warrr",
                            "name": ["id_safe"],
                            "type": "range",
                            "value": [0, 1],
                            "enlarged": False,
                            "plotType": "histogram",
                            "animationWindow": "free",
                            "yAxis": None,
                            "speed": 1,
                        },
                    ],
                    "layers": [
                        {
                            "id": "sht5ika",
                            "type": "point",
                            "config": {
                                "dataId": "anon_locs",
                                "label": "Dots",
                                "color": [255, 153, 31],
                                "highlightColor": [252, 242, 26, 255],
                                "columns": {"lat": "lat1", "lng": "lon1", "altitude": None},
                                "isVisible": True,
                                "visConfig": {
                                    "radius": 1,
                                    "fixedRadius": False,
                                    "opacity": 0.8,
                                    "outline": True,
                                    "thickness": 2,
                                    "strokeColor": [25, 20, 16],
                                    "colorRange": {
                                        "name": "Uber Viz Qualitative 4",
                                        "type": "qualitative",
                                        "category": "Uber",
                                        "colors": [
                                            "#12939A",
                                            "#DDB27C",
                                            "#88572C",
                                            "#FF991F",
                                            "#F15C17",
                                            "#223F9A",
                                            "#DA70BF",
                                            "#125C77",
                                            "#4DC19C",
                                            "#776E57",
                                            "#17B8BE",
                                            "#F6D18A",
                                            "#B7885E",
                                            "#FFCB99",
                                            "#F89570",
                                            "#829AE3",
                                            "#E79FD5",
                                            "#1E96BE",
                                            "#89DAC1",
                                            "#B3AD9E",
                                        ],
                                    },
                                    "strokeColorRange": {
                                        "name": "Global Warming",
                                        "type": "sequential",
                                        "category": "Uber",
                                        "colors": ["#5A1846", "#900C3F", "#C70039", "#E3611C", "#F1920E", "#FFC300"],
                                    },
                                    "radiusRange": [0, 50],
                                    "filled": True,
                                },
                                "hidden": False,
                                "textLabel": [
                                    {
                                        "field": None,
                                        "color": [255, 255, 255],
                                        "size": 18,
                                        "offset": [0, 0],
                                        "anchor": "start",
                                        "alignment": "center",
                                    }
                                ],
                            },
                            "visualChannels": {
                                "colorField": {"name": "id", "type": "real"},
                                "colorScale": "quantile",
                                "strokeColorField": None,
                                "strokeColorScale": "quantile",
                                "sizeField": None,
                                "sizeScale": "linear",
                            },
                        },
                        {
                            "id": "zruum3f",
                            "type": "line",
                            "config": {
                                "dataId": "anon_locs",
                                "label": "Lines",
                                "color": [221, 178, 124],
                                "highlightColor": [252, 242, 26, 255],
                                "columns": {
                                    "lat0": "lat1",
                                    "lng0": "lon1",
                                    "lat1": "lat2",
                                    "lng1": "lon2",
                                    "alt0": None,
                                    "alt1": None,
                                },
                                "isVisible": True,
                                "visConfig": {
                                    "opacity": 0.8,
                                    "thickness": 5,
                                    "colorRange": {
                                        "name": "UberPool",
                                        "type": "diverging",
                                        "category": "Uber",
                                        "colors": [
                                            "#223F9A",
                                            "#2C51BE",
                                            "#482BBD",
                                            "#7A0DA6",
                                            "#AE0E7F",
                                            "#CF1750",
                                            "#E31A1A",
                                            "#FD7900",
                                            "#FAC200",
                                            "#FAE300",
                                        ],
                                    },
                                    "sizeRange": [0, 10],
                                    "targetColor": None,
                                    "elevationScale": 1,
                                },
                                "hidden": False,
                                "textLabel": [
                                    {
                                        "field": None,
                                        "color": [255, 255, 255],
                                        "size": 18,
                                        "offset": [0, 0],
                                        "anchor": "start",
                                        "alignment": "center",
                                    }
                                ],
                            },
                            "visualChannels": {
                                "colorField": {"name": "line_p", "type": "integer"},
                                "colorScale": "quantile",
                                "sizeField": None,
                                "sizeScale": "linear",
                            },
                        },
                        {
                            "id": "a7i22im",
                            "type": "point",
                            "config": {
                                "dataId": "anon_locs",
                                "label": "Centers",
                                "color": [218, 112, 191],
                                "highlightColor": [252, 242, 26, 255],
                                "columns": {"lat": "lat2", "lng": "lon2", "altitude": None},
                                "isVisible": True,
                                "visConfig": {
                                    "radius": 2,
                                    "fixedRadius": False,
                                    "opacity": 0.8,
                                    "outline": True,
                                    "thickness": 2,
                                    "strokeColor": [25, 20, 16],
                                    "colorRange": {
                                        "name": "UberPool",
                                        "type": "diverging",
                                        "category": "Uber",
                                        "colors": [
                                            "#223F9A",
                                            "#2C51BE",
                                            "#482BBD",
                                            "#7A0DA6",
                                            "#AE0E7F",
                                            "#CF1750",
                                            "#E31A1A",
                                            "#FD7900",
                                            "#FAC200",
                                            "#FAE300",
                                        ],
                                    },
                                    "strokeColorRange": {
                                        "name": "Global Warming",
                                        "type": "sequential",
                                        "category": "Uber",
                                        "colors": ["#5A1846", "#900C3F", "#C70039", "#E3611C", "#F1920E", "#FFC300"],
                                    },
                                    "radiusRange": [0, 50],
                                    "filled": True,
                                },
                                "hidden": False,
                                "textLabel": [
                                    {
                                        "field": None,
                                        "color": [255, 255, 255],
                                        "size": 18,
                                        "offset": [0, 0],
                                        "anchor": "start",
                                        "alignment": "center",
                                    }
                                ],
                            },
                            "visualChannels": {
                                "colorField": {"name": "center_p", "type": "integer"},
                                "colorScale": "quantile",
                                "strokeColorField": None,
                                "strokeColorScale": "quantile",
                                "sizeField": None,
                                "sizeScale": "linear",
                            },
                        },
                        {
                            "id": "xvdqe8k",
                            "type": "hexagonId",
                            "config": {
                                "dataId": "h3_levels",
                                "label": "H3 Cells",
                                "color": [18, 92, 119],
                                "highlightColor": [252, 242, 26, 255],
                                "columns": {"hex_id": "h3_id"},
                                "isVisible": False,
                                "visConfig": {
                                    "opacity": 0.8,
                                    "colorRange": {
                                        "name": "UberPool",
                                        "type": "diverging",
                                        "category": "Uber",
                                        "colors": [
                                            "#223F9A",
                                            "#2C51BE",
                                            "#482BBD",
                                            "#7A0DA6",
                                            "#AE0E7F",
                                            "#CF1750",
                                            "#E31A1A",
                                            "#FD7900",
                                            "#FAC200",
                                            "#FAE300",
                                        ],
                                    },
                                    "coverage": 1,
                                    "enable3d": False,
                                    "sizeRange": [0, 500],
                                    "coverageRange": [0, 1],
                                    "elevationScale": 5,
                                    "enableElevationZoomFactor": True,
                                },
                                "hidden": False,
                                "textLabel": [
                                    {
                                        "field": None,
                                        "color": [255, 255, 255],
                                        "size": 18,
                                        "offset": [0, 0],
                                        "anchor": "start",
                                        "alignment": "center",
                                    }
                                ],
                            },
                            "visualChannels": {
                                "colorField": {"name": "count", "type": "integer"},
                                "colorScale": "quantile",
                                "sizeField": None,
                                "sizeScale": "linear",
                                "coverageField": None,
                                "coverageScale": "linear",
                            },
                        },
                    ],
                    "interactionConfig": {
                        "tooltip": {
                            "fieldsToShow": {
                                "anon_locs": [
                                    {"name": "id", "format": None},
                                    {"name": "time", "format": None},
                                    {"name": "lat1", "format": None},
                                    {"name": "lon1", "format": None},
                                    {"name": "lat2", "format": None},
                                    {"name": "lon2", "format": None},
                                    {"name": "center_p", "format": None},
                                    {"name": "line_p", "format": None},
                                    {"name": "id_safe", "format": None},
                                    {"name": "loc_safe", "format": None},
                                    {"name": "unsafe", "format": None},
                                ],
                                "h3_levels": [
                                    {"name": "h3_id", "format": None},
                                    {"name": "count", "format": None},
                                    {"name": "hex_p", "format": None},
                                ],
                            },
                            "compareMode": True,
                            "compareType": "relative",
                            "enabled": True,
                        },
                        "brush": {"size": 0.5, "enabled": False},
                        "geocoder": {"enabled": False},
                        "coordinate": {"enabled": False},
                    },
                    "layerBlending": "normal",
                    "splitMaps": [],
                    "animationConfig": {"currentTime": None, "speed": 1},
                },
                "mapState": {
                    "bearing": 0,
                    "dragRotate": False,
                    "latitude": 42.16613653816541,
                    "longitude": -8.622962015120745,
                    "pitch": 0,
                    "zoom": 16.871650945219375,
                    "isSplit": False,
                },
                "mapStyle": {
                    "styleType": "light",
                    "topLayerGroups": {},
                    "visibleLayerGroups": {
                        "label": True,
                        "road": True,
                        "border": False,
                        "building": True,
                        "water": True,
                        "land": True,
                        "3d building": False,
                    },
                    "threeDBuildingColor": [218.82023004728686, 223.47597962276103, 223.47597962276103],
                    "mapStyles": {},
                },
            },
        }
