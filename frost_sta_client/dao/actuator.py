from frost_sta_client.dao import base
from frost_sta_client.model.ext.entity_type import EntityTypes


class ActuatorDao(base.BaseDao):
    """
    A data access object for operations with the Actuator entity
    """
    def __init__(self, service):
        base.BaseDao.__init__(self, service, EntityTypes["Actuator"])
