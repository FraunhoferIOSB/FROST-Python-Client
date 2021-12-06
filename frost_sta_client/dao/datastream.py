from frost_sta_client.dao import base
from frost_sta_client.model.ext.entity_type import EntityTypes


class DatastreamDao(base.BaseDao):
    """
    A data access object for operations with the Datastream entity
    """
    def __init__(self, service):
        base.BaseDao.__init__(self, service, EntityTypes["Datastream"])