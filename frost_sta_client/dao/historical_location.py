from frost_sta_client.dao import base
from frost_sta_client.model.ext.entity_type import EntityTypes


class HistoricalLocationDao(base.BaseDao):
    def __init__(self, service):
        """
        A data access object for operations with the HistoricalLocation entity
        """
        base.BaseDao.__init__(self, service, EntityTypes["HistoricalLocation"])
