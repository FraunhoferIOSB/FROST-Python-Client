"""Generated from a CSDL metadata document. Do not edit by hand.

Regenerate with frost_sta_client.generate. Equality, JSON, and
attribute access are implemented once on the runtime base classes.
"""

from frost_sta_client.runtime.entity import ComplexType, Entity, NavigationSpec, PropertySpec


class Object(ComplexType):
    """Generated complex Object."""

    __csdl_name__ = 'Object'
    __namespace__ = 'org.OGC.STA'
    __entity_set__ = None
    __key_names__ = ()
    __key_types__ = {}
    __key_name__ = None
    __key_type__ = 'Edm.String'
    __open_type__ = True
    __is_entity__ = False
    __properties__ = ()
    __navigations__ = ()


class TM_Object(ComplexType):
    """Generated complex TM_Object."""

    __csdl_name__ = 'TM_Object'
    __namespace__ = 'org.OGC.STA'
    __entity_set__ = None
    __key_names__ = ()
    __key_types__ = {}
    __key_name__ = None
    __key_type__ = 'Edm.String'
    __open_type__ = False
    __is_entity__ = False
    __properties__ = (
        PropertySpec(
            'start',
            'start',
            'Edm.DateTimeOffset',
            nullable=False,
        ),
        PropertySpec(
            'end',
            'end',
            'Edm.DateTimeOffset',
            nullable=True,
        ),
    )
    __navigations__ = ()


class TM_Period(ComplexType):
    """Generated complex TM_Period."""

    __csdl_name__ = 'TM_Period'
    __namespace__ = 'org.OGC.STA'
    __entity_set__ = None
    __key_names__ = ()
    __key_types__ = {}
    __key_name__ = None
    __key_type__ = 'Edm.String'
    __open_type__ = False
    __is_entity__ = False
    __properties__ = (
        PropertySpec(
            'start',
            'start',
            'Edm.DateTimeOffset',
            nullable=False,
        ),
        PropertySpec(
            'end',
            'end',
            'Edm.DateTimeOffset',
            nullable=False,
        ),
    )
    __navigations__ = ()


class UnitOfMeasurement(ComplexType):
    """Generated complex UnitOfMeasurement."""

    __csdl_name__ = 'UnitOfMeasurement'
    __namespace__ = 'org.OGC.STA'
    __entity_set__ = None
    __key_names__ = ()
    __key_types__ = {}
    __key_name__ = None
    __key_type__ = 'Edm.String'
    __open_type__ = False
    __is_entity__ = False
    __properties__ = (
        PropertySpec(
            'name',
            'name',
            'Edm.String',
            nullable=True,
        ),
        PropertySpec(
            'definition',
            'definition',
            'Edm.String',
            nullable=True,
        ),
        PropertySpec(
            'symbol',
            'symbol',
            'Edm.String',
            nullable=True,
        ),
    )
    __navigations__ = ()


class Actuator(Entity):
    """Generated entity Actuator."""

    __csdl_name__ = 'Actuator'
    __namespace__ = 'de.FROST'
    __entity_set__ = 'Actuators'
    __key_names__ = ('id',)
    __key_types__ = {'id': 'Edm.Int64'}
    __key_name__ = 'id'
    __key_type__ = 'Edm.Int64'
    __open_type__ = False
    __is_entity__ = True
    __properties__ = (
        PropertySpec(
            'id',
            'id',
            'Edm.Int64',
            nullable=False,
        ),
        PropertySpec(
            'name',
            'name',
            'Edm.String',
            nullable=False,
        ),
        PropertySpec(
            'description',
            'description',
            'Edm.String',
            nullable=False,
        ),
        PropertySpec(
            'encodingType',
            'encoding_type',
            'Edm.String',
            nullable=False,
        ),
        PropertySpec(
            'metadata',
            'metadata',
            'Edm.Untyped',
            nullable=False,
        ),
        PropertySpec(
            'properties',
            'properties',
            'org.OGC.STA.Object',
            nullable=True,
        ),
    )
    __navigations__ = (
        NavigationSpec(
            'TaskingCapabilities',
            'tasking_capabilities',
            'de.FROST.TaskingCapability',
            collection=True,
            containment=False,
        ),
    )


class Datastream(Entity):
    """Generated entity Datastream."""

    __csdl_name__ = 'Datastream'
    __namespace__ = 'de.FROST'
    __entity_set__ = 'Datastreams'
    __key_names__ = ('id',)
    __key_types__ = {'id': 'Edm.Int64'}
    __key_name__ = 'id'
    __key_type__ = 'Edm.Int64'
    __open_type__ = False
    __is_entity__ = True
    __properties__ = (
        PropertySpec(
            'id',
            'id',
            'Edm.Int64',
            nullable=False,
        ),
        PropertySpec(
            'name',
            'name',
            'Edm.String',
            nullable=False,
        ),
        PropertySpec(
            'description',
            'description',
            'Edm.String',
            nullable=False,
        ),
        PropertySpec(
            'observationType',
            'observation_type',
            'Edm.String',
            nullable=False,
        ),
        PropertySpec(
            'unitOfMeasurement',
            'unit_of_measurement',
            'org.OGC.STA.UnitOfMeasurement',
            nullable=False,
        ),
        PropertySpec(
            'observedArea',
            'observed_area',
            'Edm.Geometry',
            nullable=True,
        ),
        PropertySpec(
            'phenomenonTime',
            'phenomenon_time',
            'org.OGC.STA.TM_Period',
            nullable=True,
        ),
        PropertySpec(
            'properties',
            'properties',
            'org.OGC.STA.Object',
            nullable=True,
        ),
        PropertySpec(
            'resultTime',
            'result_time',
            'org.OGC.STA.TM_Period',
            nullable=True,
        ),
    )
    __navigations__ = (
        NavigationSpec(
            'Observations',
            'observations',
            'de.FROST.Observation',
            collection=True,
            containment=False,
        ),
        NavigationSpec(
            'ObservedProperty',
            'observed_property',
            'de.FROST.ObservedProperty',
            collection=False,
            containment=False,
        ),
        NavigationSpec(
            'Sensor',
            'sensor',
            'de.FROST.Sensor',
            collection=False,
            containment=False,
        ),
        NavigationSpec(
            'Thing',
            'thing',
            'de.FROST.Thing',
            collection=False,
            containment=False,
        ),
    )


class FeatureOfInterest(Entity):
    """Generated entity FeatureOfInterest."""

    __csdl_name__ = 'FeatureOfInterest'
    __namespace__ = 'de.FROST'
    __entity_set__ = 'FeaturesOfInterest'
    __key_names__ = ('id',)
    __key_types__ = {'id': 'Edm.Int64'}
    __key_name__ = 'id'
    __key_type__ = 'Edm.Int64'
    __open_type__ = False
    __is_entity__ = True
    __properties__ = (
        PropertySpec(
            'id',
            'id',
            'Edm.Int64',
            nullable=False,
        ),
        PropertySpec(
            'name',
            'name',
            'Edm.String',
            nullable=False,
        ),
        PropertySpec(
            'description',
            'description',
            'Edm.String',
            nullable=False,
        ),
        PropertySpec(
            'encodingType',
            'encoding_type',
            'Edm.String',
            nullable=False,
        ),
        PropertySpec(
            'feature',
            'feature',
            'Edm.Geometry',
            nullable=False,
        ),
        PropertySpec(
            'properties',
            'properties',
            'org.OGC.STA.Object',
            nullable=True,
        ),
    )
    __navigations__ = (
        NavigationSpec(
            'Observations',
            'observations',
            'de.FROST.Observation',
            collection=True,
            containment=False,
        ),
    )


class HistoricalLocation(Entity):
    """Generated entity HistoricalLocation."""

    __csdl_name__ = 'HistoricalLocation'
    __namespace__ = 'de.FROST'
    __entity_set__ = 'HistoricalLocations'
    __key_names__ = ('id',)
    __key_types__ = {'id': 'Edm.Int64'}
    __key_name__ = 'id'
    __key_type__ = 'Edm.Int64'
    __open_type__ = False
    __is_entity__ = True
    __properties__ = (
        PropertySpec(
            'id',
            'id',
            'Edm.Int64',
            nullable=False,
        ),
        PropertySpec(
            'time',
            'time',
            'Edm.DateTimeOffset',
            nullable=False,
        ),
    )
    __navigations__ = (
        NavigationSpec(
            'Locations',
            'locations',
            'de.FROST.Location',
            collection=True,
            containment=False,
        ),
        NavigationSpec(
            'Thing',
            'thing',
            'de.FROST.Thing',
            collection=False,
            containment=False,
        ),
    )


class Location(Entity):
    """Generated entity Location."""

    __csdl_name__ = 'Location'
    __namespace__ = 'de.FROST'
    __entity_set__ = 'Locations'
    __key_names__ = ('id',)
    __key_types__ = {'id': 'Edm.Int64'}
    __key_name__ = 'id'
    __key_type__ = 'Edm.Int64'
    __open_type__ = False
    __is_entity__ = True
    __properties__ = (
        PropertySpec(
            'id',
            'id',
            'Edm.Int64',
            nullable=False,
        ),
        PropertySpec(
            'name',
            'name',
            'Edm.String',
            nullable=False,
        ),
        PropertySpec(
            'description',
            'description',
            'Edm.String',
            nullable=False,
        ),
        PropertySpec(
            'encodingType',
            'encoding_type',
            'Edm.String',
            nullable=False,
        ),
        PropertySpec(
            'location',
            'location',
            'Edm.Geometry',
            nullable=False,
        ),
        PropertySpec(
            'properties',
            'properties',
            'org.OGC.STA.Object',
            nullable=True,
        ),
    )
    __navigations__ = (
        NavigationSpec(
            'HistoricalLocations',
            'historical_locations',
            'de.FROST.HistoricalLocation',
            collection=True,
            containment=False,
        ),
        NavigationSpec(
            'Things',
            'things',
            'de.FROST.Thing',
            collection=True,
            containment=False,
        ),
    )


class MultiDatastream(Entity):
    """Generated entity MultiDatastream."""

    __csdl_name__ = 'MultiDatastream'
    __namespace__ = 'de.FROST'
    __entity_set__ = 'MultiDatastreams'
    __key_names__ = ('id',)
    __key_types__ = {'id': 'Edm.Int64'}
    __key_name__ = 'id'
    __key_type__ = 'Edm.Int64'
    __open_type__ = False
    __is_entity__ = True
    __properties__ = (
        PropertySpec(
            'id',
            'id',
            'Edm.Int64',
            nullable=False,
        ),
        PropertySpec(
            'name',
            'name',
            'Edm.String',
            nullable=False,
        ),
        PropertySpec(
            'description',
            'description',
            'Edm.String',
            nullable=False,
        ),
        PropertySpec(
            'observationType',
            'observation_type',
            'Edm.String',
            nullable=False,
        ),
        PropertySpec(
            'multiObservationDataTypes',
            'multi_observation_data_types',
            'Collection(Edm.String)',
            nullable=False,
        ),
        PropertySpec(
            'unitOfMeasurements',
            'unit_of_measurements',
            'Collection(UnitOfMeasurement)',
            nullable=False,
        ),
        PropertySpec(
            'observedArea',
            'observed_area',
            'Edm.Geometry',
            nullable=True,
        ),
        PropertySpec(
            'phenomenonTime',
            'phenomenon_time',
            'org.OGC.STA.TM_Period',
            nullable=True,
        ),
        PropertySpec(
            'properties',
            'properties',
            'org.OGC.STA.Object',
            nullable=True,
        ),
        PropertySpec(
            'resultTime',
            'result_time',
            'org.OGC.STA.TM_Period',
            nullable=True,
        ),
    )
    __navigations__ = (
        NavigationSpec(
            'Observations',
            'observations',
            'de.FROST.Observation',
            collection=True,
            containment=False,
        ),
        NavigationSpec(
            'ObservedProperties',
            'observed_properties',
            'de.FROST.ObservedProperty',
            collection=True,
            containment=False,
        ),
        NavigationSpec(
            'Sensor',
            'sensor',
            'de.FROST.Sensor',
            collection=False,
            containment=False,
        ),
        NavigationSpec(
            'Thing',
            'thing',
            'de.FROST.Thing',
            collection=False,
            containment=False,
        ),
    )


class Observation(Entity):
    """Generated entity Observation."""

    __csdl_name__ = 'Observation'
    __namespace__ = 'de.FROST'
    __entity_set__ = 'Observations'
    __key_names__ = ('id',)
    __key_types__ = {'id': 'Edm.Int64'}
    __key_name__ = 'id'
    __key_type__ = 'Edm.Int64'
    __open_type__ = False
    __is_entity__ = True
    __properties__ = (
        PropertySpec(
            'id',
            'id',
            'Edm.Int64',
            nullable=False,
        ),
        PropertySpec(
            'phenomenonTime',
            'phenomenon_time',
            'org.OGC.STA.TM_Object',
            nullable=True,
        ),
        PropertySpec(
            'resultTime',
            'result_time',
            'Edm.DateTimeOffset',
            nullable=True,
        ),
        PropertySpec(
            'result',
            'result',
            'Edm.Untyped',
            nullable=True,
        ),
        PropertySpec(
            'resultQuality',
            'result_quality',
            'Edm.Untyped',
            nullable=True,
        ),
        PropertySpec(
            'validTime',
            'valid_time',
            'org.OGC.STA.TM_Period',
            nullable=True,
        ),
        PropertySpec(
            'parameters',
            'parameters',
            'org.OGC.STA.Object',
            nullable=True,
        ),
    )
    __navigations__ = (
        NavigationSpec(
            'Datastream',
            'datastream',
            'de.FROST.Datastream',
            collection=False,
            containment=False,
        ),
        NavigationSpec(
            'FeatureOfInterest',
            'feature_of_interest',
            'de.FROST.FeatureOfInterest',
            collection=False,
            containment=False,
        ),
        NavigationSpec(
            'MultiDatastream',
            'multi_datastream',
            'de.FROST.MultiDatastream',
            collection=False,
            containment=False,
        ),
    )


class ObservedProperty(Entity):
    """Generated entity ObservedProperty."""

    __csdl_name__ = 'ObservedProperty'
    __namespace__ = 'de.FROST'
    __entity_set__ = 'ObservedProperties'
    __key_names__ = ('id',)
    __key_types__ = {'id': 'Edm.Int64'}
    __key_name__ = 'id'
    __key_type__ = 'Edm.Int64'
    __open_type__ = False
    __is_entity__ = True
    __properties__ = (
        PropertySpec(
            'id',
            'id',
            'Edm.Int64',
            nullable=False,
        ),
        PropertySpec(
            'name',
            'name',
            'Edm.String',
            nullable=False,
        ),
        PropertySpec(
            'definition',
            'definition',
            'Edm.String',
            nullable=False,
        ),
        PropertySpec(
            'description',
            'description',
            'Edm.String',
            nullable=False,
        ),
        PropertySpec(
            'properties',
            'properties',
            'org.OGC.STA.Object',
            nullable=True,
        ),
    )
    __navigations__ = (
        NavigationSpec(
            'Datastreams',
            'datastreams',
            'de.FROST.Datastream',
            collection=True,
            containment=False,
        ),
        NavigationSpec(
            'MultiDatastreams',
            'multi_datastreams',
            'de.FROST.MultiDatastream',
            collection=True,
            containment=False,
        ),
    )


class Sensor(Entity):
    """Generated entity Sensor."""

    __csdl_name__ = 'Sensor'
    __namespace__ = 'de.FROST'
    __entity_set__ = 'Sensors'
    __key_names__ = ('id',)
    __key_types__ = {'id': 'Edm.Int64'}
    __key_name__ = 'id'
    __key_type__ = 'Edm.Int64'
    __open_type__ = False
    __is_entity__ = True
    __properties__ = (
        PropertySpec(
            'id',
            'id',
            'Edm.Int64',
            nullable=False,
        ),
        PropertySpec(
            'name',
            'name',
            'Edm.String',
            nullable=False,
        ),
        PropertySpec(
            'description',
            'description',
            'Edm.String',
            nullable=False,
        ),
        PropertySpec(
            'encodingType',
            'encoding_type',
            'Edm.String',
            nullable=False,
        ),
        PropertySpec(
            'metadata',
            'metadata',
            'Edm.Untyped',
            nullable=False,
        ),
        PropertySpec(
            'properties',
            'properties',
            'org.OGC.STA.Object',
            nullable=True,
        ),
    )
    __navigations__ = (
        NavigationSpec(
            'Datastreams',
            'datastreams',
            'de.FROST.Datastream',
            collection=True,
            containment=False,
        ),
        NavigationSpec(
            'MultiDatastreams',
            'multi_datastreams',
            'de.FROST.MultiDatastream',
            collection=True,
            containment=False,
        ),
    )


class Task(Entity):
    """Generated entity Task."""

    __csdl_name__ = 'Task'
    __namespace__ = 'de.FROST'
    __entity_set__ = 'Tasks'
    __key_names__ = ('id',)
    __key_types__ = {'id': 'Edm.Int64'}
    __key_name__ = 'id'
    __key_type__ = 'Edm.Int64'
    __open_type__ = False
    __is_entity__ = True
    __properties__ = (
        PropertySpec(
            'id',
            'id',
            'Edm.Int64',
            nullable=False,
        ),
        PropertySpec(
            'creationTime',
            'creation_time',
            'Edm.DateTimeOffset',
            nullable=True,
        ),
        PropertySpec(
            'taskingParameters',
            'tasking_parameters',
            'org.OGC.STA.Object',
            nullable=False,
        ),
    )
    __navigations__ = (
        NavigationSpec(
            'TaskingCapability',
            'tasking_capability',
            'de.FROST.TaskingCapability',
            collection=False,
            containment=False,
        ),
    )


class TaskingCapability(Entity):
    """Generated entity TaskingCapability."""

    __csdl_name__ = 'TaskingCapability'
    __namespace__ = 'de.FROST'
    __entity_set__ = 'TaskingCapabilities'
    __key_names__ = ('id',)
    __key_types__ = {'id': 'Edm.Int64'}
    __key_name__ = 'id'
    __key_type__ = 'Edm.Int64'
    __open_type__ = False
    __is_entity__ = True
    __properties__ = (
        PropertySpec(
            'id',
            'id',
            'Edm.Int64',
            nullable=False,
        ),
        PropertySpec(
            'name',
            'name',
            'Edm.String',
            nullable=False,
        ),
        PropertySpec(
            'description',
            'description',
            'Edm.String',
            nullable=False,
        ),
        PropertySpec(
            'properties',
            'properties',
            'org.OGC.STA.Object',
            nullable=True,
        ),
        PropertySpec(
            'taskingParameters',
            'tasking_parameters',
            'org.OGC.STA.Object',
            nullable=False,
        ),
    )
    __navigations__ = (
        NavigationSpec(
            'Actuator',
            'actuator',
            'de.FROST.Actuator',
            collection=False,
            containment=False,
        ),
        NavigationSpec(
            'Tasks',
            'tasks',
            'de.FROST.Task',
            collection=True,
            containment=False,
        ),
        NavigationSpec(
            'Thing',
            'thing',
            'de.FROST.Thing',
            collection=False,
            containment=False,
        ),
    )


class Thing(Entity):
    """Generated entity Thing."""

    __csdl_name__ = 'Thing'
    __namespace__ = 'de.FROST'
    __entity_set__ = 'Things'
    __key_names__ = ('id',)
    __key_types__ = {'id': 'Edm.Int64'}
    __key_name__ = 'id'
    __key_type__ = 'Edm.Int64'
    __open_type__ = False
    __is_entity__ = True
    __properties__ = (
        PropertySpec(
            'id',
            'id',
            'Edm.Int64',
            nullable=False,
        ),
        PropertySpec(
            'name',
            'name',
            'Edm.String',
            nullable=False,
        ),
        PropertySpec(
            'description',
            'description',
            'Edm.String',
            nullable=False,
        ),
        PropertySpec(
            'properties',
            'properties',
            'org.OGC.STA.Object',
            nullable=True,
        ),
    )
    __navigations__ = (
        NavigationSpec(
            'HistoricalLocations',
            'historical_locations',
            'de.FROST.HistoricalLocation',
            collection=True,
            containment=False,
        ),
        NavigationSpec(
            'Locations',
            'locations',
            'de.FROST.Location',
            collection=True,
            containment=False,
        ),
        NavigationSpec(
            'MultiDatastreams',
            'multi_datastreams',
            'de.FROST.MultiDatastream',
            collection=True,
            containment=False,
        ),
        NavigationSpec(
            'TaskingCapabilities',
            'tasking_capabilities',
            'de.FROST.TaskingCapability',
            collection=True,
            containment=False,
        ),
        NavigationSpec(
            'Datastreams',
            'datastreams',
            'de.FROST.Datastream',
            collection=True,
            containment=False,
        ),
    )


TYPES = {
    'org.OGC.STA.Object': Object,
    'Object': Object,
    'org.OGC.STA.TM_Object': TM_Object,
    'TM_Object': TM_Object,
    'org.OGC.STA.TM_Period': TM_Period,
    'TM_Period': TM_Period,
    'org.OGC.STA.UnitOfMeasurement': UnitOfMeasurement,
    'UnitOfMeasurement': UnitOfMeasurement,
    'de.FROST.Actuator': Actuator,
    'Actuator': Actuator,
    'de.FROST.Datastream': Datastream,
    'Datastream': Datastream,
    'de.FROST.FeatureOfInterest': FeatureOfInterest,
    'FeatureOfInterest': FeatureOfInterest,
    'de.FROST.HistoricalLocation': HistoricalLocation,
    'HistoricalLocation': HistoricalLocation,
    'de.FROST.Location': Location,
    'Location': Location,
    'de.FROST.MultiDatastream': MultiDatastream,
    'MultiDatastream': MultiDatastream,
    'de.FROST.Observation': Observation,
    'Observation': Observation,
    'de.FROST.ObservedProperty': ObservedProperty,
    'ObservedProperty': ObservedProperty,
    'de.FROST.Sensor': Sensor,
    'Sensor': Sensor,
    'de.FROST.Task': Task,
    'Task': Task,
    'de.FROST.TaskingCapability': TaskingCapability,
    'TaskingCapability': TaskingCapability,
    'de.FROST.Thing': Thing,
    'Thing': Thing,
}

ENTITY_SETS = {
    'actuators': ('Actuators', Actuator),
    'datastreams': ('Datastreams', Datastream),
    'features_of_interest': ('FeaturesOfInterest', FeatureOfInterest),
    'historical_locations': ('HistoricalLocations', HistoricalLocation),
    'locations': ('Locations', Location),
    'multi_datastreams': ('MultiDatastreams', MultiDatastream),
    'observations': ('Observations', Observation),
    'observed_properties': ('ObservedProperties', ObservedProperty),
    'sensors': ('Sensors', Sensor),
    'tasks': ('Tasks', Task),
    'tasking_capabilities': ('TaskingCapabilities', TaskingCapability),
    'things': ('Things', Thing),
}

ACTIONS = (
)

FUNCTIONS = (
)
