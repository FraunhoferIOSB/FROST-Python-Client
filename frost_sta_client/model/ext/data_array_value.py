# Copyright (C) 2021 Fraunhofer Institut IOSB, Fraunhoferstr. 1, D 76131
# Karlsruhe, Germany.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from enum import Enum

import frost_sta_client
import datetime


class DataArrayValue:

    class Property(Enum):
        ID = 1
        PHENOMENON_TIME = 2
        RESULT = 3
        RESULT_TIME = 4
        RESULT_QUALITY = 5
        VALID_TIME = 6
        PARAMETERS = 7
        FEATURE_OF_INTEREST = 8

        def to_string(self):
            if self is DataArrayValue.Property.ID:
                return "id"
            if self is DataArrayValue.Property.PHENOMENON_TIME:
                return "phenomenonTime"
            if self is DataArrayValue.Property.RESULT:
                return "result"
            if self is DataArrayValue.Property.RESULT_TIME:
                return "resultTime"
            if self is DataArrayValue.Property.RESULT_QUALITY:
                return "resultQuality"
            if self is DataArrayValue.Property.VALID_TIME:
                return "validTime"
            if self is DataArrayValue.Property.PARAMETERS:
                return "parameters"
            if self is DataArrayValue.Property.FEATURE_OF_INTEREST:
                return "FeatureOfInterest/id"


    class VisibleProperties:
        def __init__(self, all_values: bool):
            self.id = all_values
            self.phenomenon_time = all_values
            self.result = all_values
            self.result_time = all_values
            self.result_quality = all_values
            self.valid_time = all_values
            self.parameters = all_values
            self.feature_of_interest = all_values

        def __init__(self):
            self = DataArrayValue.VisibleProperties(False)

        def __init__(self, select):
            self.id = DataArrayValue.Property.ID in select
            self.phenomenon_time = DataArrayValue.Property.PHENOMENON_TIME in select
            self.result = DataArrayValue.Property.RESULT in select
            self.result_time = DataArrayValue.Property.RESULT_TIME in select
            self.result_quality = DataArrayValue.Property.RESULT_QUALITY in select
            self.valid_time = DataArrayValue.Property.VALID_TIME in select
            self.parameters = DataArrayValue.Property.PARAMETERS in select
            self.feature_of_interest = DataArrayValue.Property.FEATURE_OF_INTEREST in select

        def get_components(self):
            components = []
            if self.id:
                components.append(DataArrayValue.Property.ID.to_string())
            if self.phenomenon_time:
                components.append(DataArrayValue.Property.PHENOMENON_TIME.to_string())
            if self.result:
                components.append(DataArrayValue.Property.RESULT.to_string())
            if self.result_time:
                components.append(DataArrayValue.Property.RESULT_TIME.to_string())
            if self.result_quality:
                components.append(DataArrayValue.Property.RESULT_QUALITY.to_string())
            if self.valid_time:
                components.append(DataArrayValue.Property.VALID_TIME.to_string())
            if self.parameters:
                components.append(DataArrayValue.Property.PARAMETERS.to_string())
            if self.feature_of_interest:
                components.append(DataArrayValue.Property.FEATURE_OF_INTEREST.to_string())
            return components


        def from_observation(self, o: frost_sta_client.Observation):
            value = []
            if self.id:
                value.append(o.id)
            if self.phenomenon_time:
                if type(o.phenomenon_time) == str:
                    value.append(o.phenomenon_time)
                if type(o.phenomenon_time) == datetime.datetime:
                    value.append(o.phenomenon_time.isoformat())
            if self.result:
                value.append(o.result)
            if self.result_time:
                value.append(o.result_time)
            if self.result_quality:
                value.append(o.result_quality)
            if self.valid_time:
                value.append(o.valid_time)
            if self.parameters:
                value.append(o.parameters)
            if self.feature_of_interest:
                value.append(o.feature_of_interest.id)
            return value


    def __init__(self):
        self.datastream = None
        self.multi_datastream = None
        self.visible_properties = None
        self.data_array = []
        self.components = None
        self.observations = []


    @property
    def datastream(self):
        return self._datastream

    @datastream.setter
    def datastream(self, value):
        self._datastream = value

    @property
    def components(self):
        return self._components

    @components.setter
    def components(self, properties):
        if properties is None:
            self._components = None
            return
        if len(self.data_array) >= 1:
            raise ValueError("Can not change components after adding Observations")
        self.visible_properties = self.VisibleProperties(properties)
        self._components = self.visible_properties.get_components()

    @property
    def data_array(self):
        return self._data_array

    @data_array.setter
    def data_array(self, value):
        self._data_array = value

    def add_observation(self, o):
        self.data_array.append(self.visible_properties.from_observation(o))
        self.observations.append(o)

    def __getstate__(self):
        data = {"Datastream": {
                "@iot.id": self.datastream.id
                },
                "components": self.components,
                "dataArray": self.data_array}
        return data

