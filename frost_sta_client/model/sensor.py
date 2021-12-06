from frost_sta_client.dao.sensor import SensorDao

from . import entity
from . import datastream
from . import multi_datastream

from frost_sta_client import utils
from .ext import entity_type
from .ext import entity_list


class Sensor(entity.Entity):

    def __init__(self,
                 name='',
                 description='',
                 encoding_type='',
                 properties=None,
                 metadata='',
                 datastreams=None,
                 multi_datastreams=None):
        super().__init__()
        if properties is None:
            properties = {}
        self.name = name
        self.description = description
        self.properties = properties
        self.encoding_type = encoding_type
        self.metadata = metadata
        self.datastreams = datastreams
        self.multi_datastreams = multi_datastreams

    def __new__(cls, *args, **kwargs):
        new_sensor = super().__new__(cls)
        attributes = {'_id': None, '_name': '', '_description': '', '_properties': {}, '_encoding_type': '',
                      '_metadata': '', '_datastreams': None, '_multi_datastreams': None, '_self_link': '',
                      '_service': None}
        for key, value in attributes.items():
            new_sensor.__dict__[key] = value
        return new_sensor

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if type(value) != str:
            raise ValueError('name should be of type str!')
        self._name = value

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value):
        if type(value) != str:
            raise ValueError('description should be of type str!')
        self._description = value

    @property
    def properties(self):
        return self._properties

    @properties.setter
    def properties(self, value):
        if type(value) != dict:
            raise ValueError('properties should be of type dict!')
        self._properties = value

    @property
    def encoding_type(self):
        return self._encoding_type

    @encoding_type.setter
    def encoding_type(self, value):
        if type(value) != str:
            raise ValueError('encoding_type should be of type str!')
        self._encoding_type = value

    @property
    def metadata(self):
        return self._metadata

    @metadata.setter
    def metadata(self, value):
        if type(value) != str:
            raise ValueError('metadata should be of type str!')
        self._metadata = value

    @property
    def datastreams(self):
        return self._datastreams
    
    @datastreams.setter
    def datastreams(self, values):
        if values is None:
            self._datastreams = None
            return
        if type(values) != entity_list.EntityList or\
                any((not isinstance(ds, datastream.Datastream)) for ds in values):
            raise ValueError('datastreams should be an entity list of datastreams!')
        self._datastreams = values

    @property
    def multi_datastreams(self):
        return self._multi_datastreams

    @multi_datastreams.setter
    def multi_datastreams(self, values):
        if values is None:
            self._multi_datastreams = None
            return
        if type(values) != entity_list.EntityList or\
                any((not isinstance(mds, multi_datastream.MultiDatastream)) for mds in values):
            raise ValueError('multi_datastreams should be a list of multi_datastreams!')
        self._multi_datastreams = values

    def ensure_service_on_children(self, service):
        if self.datastreams is not None:
            self.datastreams.set_service(service)
        if self.multi_datastreams is not None:
            self.multi_datastreams.set_service(service)

    def __eq__(self, other):
        if other is None:
            return False
        if not isinstance(other, type(self)):
            return False
        if id(self) == id(other):
            return True
        if self.name != other.name:
            return False
        if self.description != other.description:
            return False
        if self.encoding_type != other.encoding_type:
            return False
        if self.properties != other.properties:
            return False
        if self.metadata != other.metadata:
            return False
        return True

    def __ne__(self, other):
        return not self == other

    def __getstate__(self):
        _data = super().__getstate__()
        _data['name'] = self._name
        _data['description'] = self._description
        _data['properties'] = self._properties
        _data['encodingType'] = self._encoding_type
        _data['metadata'] = self._metadata
        if self.datastreams is not None and len(self._datastreams.entities) > 0:
            _data['Datastreams'] = self._datastreams.__getstate__()
        if self.multi_datastreams is not None and len(self.multi_datastreams.entities) > 0:
            _data['MultiDatastreams'] = self._multi_datastreams.__getstate__()
        return _data

    def __setstate__(self, state):
        super().__setstate__(state)
        self.name = state.get('name', '')
        self.description = state.get('description', '')
        self.encoding_type = state.get('encodingType', '')
        self.meta_data = state.get('metadata', '')
        self.properties = state.get('properties', {})
        if state.get('Datastreams', None) is not None:
            entity_class = entity_type.EntityTypes['Datastream']['class']
            self.datastreams = utils.transform_json_to_entity_list(state['Datastreams'], entity_class)
            self.datastreams.next_link = state.get('Datastreams@iot.nextLink', None)
        if state.get('MultiDatastreams', None) is not None:
            entity_class = entity_type.EntityTypes['MultiDatastream']['class']
            self.multi_datastreams = utils.transform_json_to_entity_list(state['MultiDatastreams'], entity_class)
            self.multi_datastreams.next_link = state.get('MultiDatastreams@iot.nextLink', None)

    def get_dao(self, service):
        return SensorDao(service)
