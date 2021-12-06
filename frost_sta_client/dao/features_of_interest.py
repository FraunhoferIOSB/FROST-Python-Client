from frost_sta_client.dao import base
from frost_sta_client.model.ext.entity_type import EntityTypes


class FeaturesOfInterestDao(base.BaseDao):
    """
    A data access object for operations with the FeatureOfInterest entity
    """
    def __init__(self, service):
        base.BaseDao.__init__(self, service, EntityTypes["FeatureOfInterest"])
