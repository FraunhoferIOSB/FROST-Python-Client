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

import json

import frost_sta_client.model
from . import entity
from . import multi_datastream
from . import datastream
from . import feature_of_interest

from frost_sta_client.dao.observation import ObservationDao

from frost_sta_client import utils


class Observation(entity.Entity):

    def __init__(self,
                 phenomenon_time=None,
                 result=None,
                 result_time=None,
                 result_quality=None,
                 valid_time=None,
                 parameters=None,
                 datastream=None,
                 multi_datastream=None,
                 feature_of_interest=None,
                 **kwargs):
        super().__init__(kwargs.get('id', ''), kwargs.get('selfLink', ''))
        if parameters is None:
            parameters = {}
        self.phenomenon_time = phenomenon_time
        self.result = result
        self.result_time = result_time
        self.result_quality = result_quality
        self.valid_time = valid_time
        self.parameters = parameters
        self.datastream = datastream
        self.multi_datastream = multi_datastream
        self.feature_of_interest = feature_of_interest

    def __new__(cls, *args, **kwargs):
        new_observation = super().__new__(cls)
        attributes = {'_id': None, '_phenomenon_time': None, '_result': None, '_result_time': None,
                      '_result_quality': None, '_valid_time': None, '_parameters': {}, '_datastream': None,
                      '_multi_datastream': None, '_feature_of_interest': None, '_self_link': '', '_service': None}
        for key, value in attributes.items():
            new_observation.__dict__[key] = value
        return new_observation

    @property
    def phenomenon_time(self):
        return self._phenomenon_time

    @phenomenon_time.setter
    def phenomenon_time(self, value):
        self._phenomenon_time = utils.process_datetime(value)

    @property
    def result(self):
        return self._result

    @result.setter
    def result(self, value):
        if value is None:
            self._result = None
            return
        try:
            json.dumps(value)
        except TypeError:
            raise TypeError('result should be json serializable')
        self._result = value
    
    @property
    def result_time(self):
        return self._result_time

    @result_time.setter
    def result_time(self, value):
        self._result_time = utils.process_datetime(value)

    @property
    def result_quality(self):
        return self._result_quality

    @result_quality.setter
    def result_quality(self, value):
        if value is None:
            self._result_quality = None
            return
        try:
            json.dumps(value)
        except TypeError:
            raise TypeError('result_quality should be json serializable')
        self._result_quality = value

    @property
    def valid_time(self):
        return self._valid_time

    @valid_time.setter
    def valid_time(self, value):
        self._valid_time = utils.process_datetime(value)

    @property
    def parameters(self):
        return self._parameters

    @parameters.setter
    def parameters(self, values):
        if values is None:
            self._parameters = None
            return
        if type(values) != dict:
            raise ValueError('parameters should be of type dict!')
        self._parameters = values
    
    @property
    def feature_of_interest(self):
        return self._feature_of_interest

    @feature_of_interest.setter
    def feature_of_interest(self, value):
        if value is None:
            self._feature_of_interest = None
            return
        if type(value) != feature_of_interest.FeatureOfInterest:
            raise ValueError('feature_of_interest should be of type FeatureOfInterest!')
        self._feature_of_interest = value

    @property
    def datastream(self):
        return self._datastream

    @datastream.setter
    def datastream(self, value):
        if value is None:
            self._datastream = None
            return
        if type(value) != datastream.Datastream:
            raise ValueError('datastream should be of type Datastream!')
        self._datastream = value

    @property
    def multi_datastream(self):
        return self._multi_datastream

    @multi_datastream.setter
    def multi_datastream(self, value):
        if value is None:
            self._multi_datastream = None
            return
        if type(value) == multi_datastream.MultiDatastream:
            self._multi_datastream = value
            return
        raise ValueError('multi_datastream should be of type MultiDatastream!')

    def ensure_service_on_children(self, service):
        if self.datastream is not None:
            self.datastream.set_service(service)
        if self.multi_datastream is not None:
            self.multi_datastream.set_service(service)
        if self.feature_of_interest is not None:
            self.feature_of_interest.set_service(service)

    def __eq__(self, other):
        if other is None:
            return False
        if not isinstance(other, type(self)):
            return False
        if id(self) == id(other):
            return True
        if self.result != other.result:
            return False
        if self.phenomenon_time != other.phenomenon_time:
            return False
        if self.result_time != other.result_time:
            return False
        if self.valid_time != other.valid_time:
            return False
        if self.parameters != other.parameters:
            return False
        if self.result_quality != other.result_quality:
            return False
        return True

    def __ne__(self, other):
        return not self == other

    def __getstate__(self):
        data = super().__getstate__()
        if self.parameters is not None and self.parameters != {}:
            data['parameters'] = self.parameters
        if self.result is not None:
            data['result'] = self.result
        if self.result_quality is not None:
            data['resultQuality'] = self.result_quality
        if self.phenomenon_time is not None:
            data['phenomenonTime'] = self.phenomenon_time
        if self.result_time is not None:
            data['resultTime'] = self.result_time
        if self.valid_time is not None:
            data['validTime'] = self.valid_time
        if self.datastream is not None:
            data['Datastream'] = self.datastream.__getstate__()
        if self.multi_datastream is not None:
            data['MultiDatastream'] = self.multi_datastream.__getstate__()
        if self.feature_of_interest is not None:
            data['FeatureOfInterest'] = self.feature_of_interest.__getstate__()
        return data

    def __setstate__(self, state):
        super().__setstate__(state)
        self.parameters = state.get("parameters", {})
        self.result = state.get("result", None)
        self.result_quality = state.get("resultQuality", None)
        self.phenomenon_time = state.get("phenomenonTime", None)
        self.result_time = state.get("resultTime", None)
        self.valid_time = state.get("validTime", None)
        if state.get('Datastream', None) is not None:
            self.datastream = frost_sta_client.model.datastream.Datastream()
            self.datastream.__setstate__(state['Datastream'])
        if state.get('MultiDatastream', None) is not None:
            self.multi_datastream = frost_sta_client.model.multi_datastream.MultiDatastream()
            self.multi_datastream.__setstate__(state['MultiDatastream'])
        if state.get("FeatureOfInterest", None) is not None:
            self.feature_of_interest = frost_sta_client.model.feature_of_interest.FeatureOfInterest()
            self.feature_of_interest.__setstate__(state['FeatureOfInterest'])




    def get_dao(self, service):
        return ObservationDao(service)
