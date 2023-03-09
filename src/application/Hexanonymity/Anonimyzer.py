import pandas as pd
from abc import ABC, abstractmethod


class Anonimyzer(ABC):
    '''
    * Class from which all implementations of anonimization algorithms derive
    * The parameters of the algorithm will be passed at the constructor of every subclass
    * Parameters must not vary dependig on the format of the dataframe 
    '''

    @abstractmethod
    def apply(self, locs: pd.DataFrame, id_col: str, lat_col: str, lon_col: str, *critical_cols: str) -> pd.DataFrame:
        '''
        Performs an anonimization over a dataframe
        * Needs the location of specific columns in the dataframe 
            - These are the column names in `main_cols` parameter
        * Returns an anonimyzed dataframe, without modifying the original one
        * It applies a clustering strategy
            - Some rows of are cluster members and others (much less) are cluster centers
        * A cluster member has only one associated cluster center
        * A cluster member acquires the properties of it's cluster center which are considered sensible, besides latitude and longitude
            - These are the column names in `critical_cols` parameter
        '''
        pass

    @abstractmethod
    def apply_debug(self, locs: pd.DataFrame, id_col: str, lat_col: str, lon_col: str, time_col: str) -> pd.DataFrame:
        '''
        Same procedure as the ``apply`` method 
        * Returns a dataframe with detailed information about the execution
        * The shape of the dataframe is the following:
                - `id` -> the unique id of the entity sending the location
                - `time` -> the timestamp when the location was sent
                - `lat1`, `lon1` and `lat2`, `lon2` -> coordinates of the entity before and after the anonimization
                - `center_p` and `line_p` -> the precision of a cluster or a location when joining a cluster
                - `id_safe`, `loc_safe`, `unsafe` -> exclusive flag to show the quality of the grouping
        '''
        pass

    @property
    def kepler_config(self) -> dict:
        '''
        Configuration object for correctly display in keplergl the dataframe returned by `apply_debug`
        '''
        return {'version': 'v1', 'config': {'visState': {'filters': [{'dataId': ['h3_levels'], 'id': '4f1r8uoo8', 'name': ['hex_p'], 'type': 'range', 'value': [10, 13], 'enlarged': False, 'plotType': 'histogram', 'animationWindow': 'free', 'yAxis': None, 'speed': 1}, {'dataId': ['anon_locs'], 'id': 'unahvxar', 'name': ['time'], 'type': 'timeRange', 'value': [1642750743000, 1642751400000], 'enlarged': False, 'plotType': 'histogram', 'animationWindow': 'free', 'yAxis': None, 'speed': 1}], 'layers': [{'id': 'sht5ika', 'type': 'point', 'config': {'dataId': 'anon_locs', 'label': 'Dots', 'color': [255, 153, 31], 'highlightColor': [252, 242, 26, 255], 'columns': {'lat': 'lat1', 'lng': 'lon1', 'altitude': None}, 'isVisible': True, 'visConfig': {'radius': 1, 'fixedRadius': False, 'opacity': 0.8, 'outline': True, 'thickness': 2, 'strokeColor': [25, 20, 16], 'colorRange': {'name': 'Uber Viz Qualitative 4', 'type': 'qualitative', 'category': 'Uber', 'colors': ['#12939A', '#DDB27C', '#88572C', '#FF991F', '#F15C17', '#223F9A', '#DA70BF', '#125C77', '#4DC19C', '#776E57', '#17B8BE', '#F6D18A', '#B7885E', '#FFCB99', '#F89570', '#829AE3', '#E79FD5', '#1E96BE', '#89DAC1', '#B3AD9E']}, 'strokeColorRange': {'name': 'Global Warming', 'type': 'sequential', 'category': 'Uber', 'colors': ['#5A1846', '#900C3F', '#C70039', '#E3611C', '#F1920E', '#FFC300']}, 'radiusRange': [0, 50], 'filled': True}, 'hidden': False, 'textLabel': [{'field': None, 'color': [255, 255, 255], 'size': 18, 'offset': [0, 0], 'anchor': 'start', 'alignment': 'center'}]}, 'visualChannels': {'colorField': {'name': 'id', 'type': 'real'}, 'colorScale': 'quantile', 'strokeColorField': None, 'strokeColorScale': 'quantile', 'sizeField': None, 'sizeScale': 'linear'}}, {'id': 'zruum3f', 'type': 'line', 'config': {'dataId': 'anon_locs', 'label': 'Lines', 'color': [221, 178, 124], 'highlightColor': [252, 242, 26, 255], 'columns': {'lat0': 'lat1', 'lng0': 'lon1', 'lat1': 'lat2', 'lng1': 'lon2', 'alt0': None, 'alt1': None}, 'isVisible': True, 'visConfig': {'opacity': 0.8, 'thickness': 5, 'colorRange': {'name': 'UberPool', 'type': 'diverging', 'category': 'Uber', 'colors': ['#223F9A', '#2C51BE', '#482BBD', '#7A0DA6', '#AE0E7F', '#CF1750', '#E31A1A', '#FD7900', '#FAC200', '#FAE300']}, 'sizeRange': [0, 10], 'targetColor': None, 'elevationScale': 1}, 'hidden': False, 'textLabel': [{'field': None, 'color': [255, 255, 255], 'size': 18, 'offset': [0, 0], 'anchor': 'start', 'alignment': 'center'}]}, 'visualChannels': {'colorField': {'name': 'line_p', 'type': 'integer'}, 'colorScale': 'quantile', 'sizeField': None, 'sizeScale': 'linear'}}, {'id': 'a7i22im', 'type': 'point', 'config': {'dataId': 'anon_locs', 'label': 'Centers', 'color': [218, 112, 191], 'highlightColor': [252, 242, 26, 255], 'columns': {'lat': 'lat2', 'lng': 'lon2', 'altitude': None}, 'isVisible': True, 'visConfig': {'radius': 2, 'fixedRadius': False, 'opacity': 0.8, 'outline': True, 'thickness': 2, 'strokeColor': [25, 20, 16], 'colorRange': {'name': 'UberPool', 'type': 'diverging', 'category': 'Uber', 'colors': ['#223F9A', '#2C51BE', '#482BBD', '#7A0DA6', '#AE0E7F', '#CF1750', '#E31A1A', '#FD7900', '#FAC200', '#FAE300']}, 'strokeColorRange': {'name': 'Global Warming', 'type': 'sequential', 'category': 'Uber', 'colors': ['#5A1846', '#900C3F', '#C70039', '#E3611C', '#F1920E', '#FFC300']}, 'radiusRange': [0, 50], 'filled': True}, 'hidden': False, 'textLabel': [{'field': None, 'color': [255, 255, 255], 'size': 18, 'offset': [0, 0], 'anchor': 'start', 'alignment': 'center'}]}, 'visualChannels': {'colorField': {'name': 'center_p', 'type': 'integer'}, 'colorScale': 'quantile', 'strokeColorField': None, 'strokeColorScale': 'quantile', 'sizeField': None, 'sizeScale': 'linear'}}, {'id': 'xvdqe8k', 'type': 'hexagonId', 'config': {'dataId': 'h3_levels', 'label': 'H3 Cells', 'color': [18, 92, 119], 'highlightColor': [252, 242, 26, 255], 'columns': {'hex_id': 'h3_id'}, 'isVisible': False, 'visConfig': {'opacity': 0.8, 'colorRange': {'name': 'UberPool', 'type': 'diverging', 'category': 'Uber', 'colors': ['#223F9A', '#2C51BE', '#482BBD', '#7A0DA6', '#AE0E7F', '#CF1750', '#E31A1A', '#FD7900', '#FAC200', '#FAE300']}, 'coverage': 1, 'enable3d': False, 'sizeRange': [0, 500], 'coverageRange': [0, 1], 'elevationScale': 5, 'enableElevationZoomFactor': True}, 'hidden': False, 'textLabel': [{'field': None, 'color': [255, 255, 255], 'size': 18, 'offset': [0, 0], 'anchor': 'start', 'alignment': 'center'}]}, 'visualChannels': {'colorField': {'name': 'count', 'type': 'integer'}, 'colorScale': 'quantile', 'sizeField': None, 'sizeScale': 'linear', 'coverageField': None, 'coverageScale': 'linear'}}], 'interactionConfig': {'tooltip': {'fieldsToShow': {'anon_locs': [{'name': 'id', 'format': None}, {'name': 'time', 'format': None}, {'name': 'lat1', 'format': None}, {'name': 'lon1', 'format': None}, {'name': 'lat2', 'format': None}, {'name': 'lon2', 'format': None}, {'name': 'center_p', 'format': None}, {'name': 'line_p', 'format': None}], 'h3_levels': [{'name': 'h3_id', 'format': None}, {'name': 'count', 'format': None}, {'name': 'hex_p', 'format': None}]}, 'compareMode': False, 'compareType': 'absolute', 'enabled': True}, 'brush': {'size': 0.5, 'enabled': False}, 'geocoder': {'enabled': False}, 'coordinate': {'enabled': False}}, 'layerBlending': 'normal', 'splitMaps': [], 'animationConfig': {'currentTime': None, 'speed': 1}}, 'mapState': {'bearing': 0, 'dragRotate': False, 'latitude': 42.16613653816541, 'longitude': -8.622962015120745, 'pitch': 0, 'zoom': 16.871650945219375, 'isSplit': False}, 'mapStyle': {'styleType': 'light', 'topLayerGroups': {}, 'visibleLayerGroups': {'label': True, 'road': True, 'border': False, 'building': True, 'water': True, 'land': True, '3d building': False}, 'threeDBuildingColor': [218.82023004728686, 223.47597962276103, 223.47597962276103], 'mapStyles': {}}}}
