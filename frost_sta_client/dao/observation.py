from frost_sta_client.dao import base
from frost_sta_client.model.ext.entity_type import EntityTypes


class ObservationDao(base.BaseDao):
    def __init__(self, service):
        """
        A data access object for operations with the Observation entity
        """
        base.BaseDao.__init__(self, service, EntityTypes["Observation"])
