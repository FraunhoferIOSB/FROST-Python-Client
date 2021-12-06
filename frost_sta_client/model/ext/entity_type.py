EntityTypes = {
    'Datastream': {
        'singular': 'Datastream',
        'plural': 'Datastreams',
        'class': 'frost_sta_client.model.datastream.Datastream',
        'relations_list': ['Sensor', 'Thing', 'ObservedProperty', 'Observation']
    },
    'MultiDatastream': {
        'singular': 'MultiDatastream',
        'plural': 'MultiDatastreams',
        'class': 'frost_sta_client.model.multi_datastream.MultiDatastream',
        'relations_list': ['Sensor', 'Thing', 'ObservedProperty', 'Observation']
    },
    'FeatureOfInterest': {
        'singular': 'FeatureOfInterest',
        'plural': 'FeaturesOfInterest',
        'class': 'frost_sta_client.model.feature_of_interest.FeatureOfInterest',
        'relations_list': ['Observation']
    },
    'HistoricaLocation': {
        'singular': 'HistoricalLocation',
        'plural': 'HistoricalLocations',
        'class': 'frost_sta_client.model.historical_location.HistoricalLocation',
        'relations_list': ['Thing', 'Location']
    },
    'Actuator': {
        'singular': 'Actuator',
        'plural': 'Actuators',
        'class': 'frost_sta_client.model.actuator.Actuator',
        'relations_list': ['TaskingCapability']
    },
    'Location': {
        'singular': 'Location',
        'plural': 'Locations',
        'class': 'frost_sta_client.model.location.Location',
        'relations_list': ['Thing', 'HistoricalLocation']
    },
    'Observation': {
        'singular': 'Observation',
        'plural': 'Observations',
        'class': 'frost_sta_client.model.observation.Observation',
        'relations_list': ['FeatureOfInterest', 'Datastream', 'MultiDatastream']
    },
    'Thing': {
        'singular': 'Thing',
        'plural': 'Things',
        'class': 'frost_sta_client.model.thing.Thing',
        'relations_list': ['Datastream', 'MultiDatastream', 'Location', 'HistoricalLocation', 'TaskingCapability']
    },
    'ObservedProperty': {
        'singular': 'ObservedProperty',
        'plural': 'ObservedProperties',
        'class': 'frost_sta_client.model.observedproperty.ObservedProperty',
        'relations_list': ['Datastream', 'MultiDatastream']
    },
    'Sensor': {
        'singular': 'Sensor',
        'plural': 'Sensors',
        'class': 'frost_sta_client.model.sensor.Sensor',
        'relations_list': ['Datastream', 'MultiDatastream']
    },
    'Task': {
        'singular': 'Task',
        'plural': 'Tasks',
        'class': 'frost_sta_client.model.task.Task',
        'relations_list': ['TaskingCapability']
    },
    'TaskingCapability': {
        'singular': 'TaskingCapability',
        'plural': 'TaskingCapabilities',
        'class': 'frost_sta_client.model.tasking_capability.TaskingCapability',
        'relations_list': ['Task', 'Actuator', 'Thing']
    },
    'UnitOfMeasurement': {
        'singular': 'UnitOfMeasurement',
        'plural': 'UnitOfMeasurements',
        'class': 'frost_sta_client.model.ext.unitofmeasurement.UnitOfMeasurement'
    },
    'EntityList': {
        'singular': 'EntityList',
        'plural': 'EntityLists',
        'class': 'frost_sta_client.model.ext.entity_list.EntityList'
    }
}
