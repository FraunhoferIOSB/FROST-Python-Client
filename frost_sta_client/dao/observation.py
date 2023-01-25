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

from frost_sta_client.dao import base
from frost_sta_client.model.ext.entity_type import EntityTypes
from frost_sta_client.utils import transform_entity_to_json_dict
import frost_sta_client

import logging
import requests
import json



class ObservationDao(base.BaseDao):
    CREATE_OBSERVATIONS = "CreateObservations"

    def __init__(self, service):
        """
        A data access object for operations with the Observation entity
        """
        base.BaseDao.__init__(self, service, EntityTypes["Observation"])

    def create(self, entity):
        if isinstance(entity, frost_sta_client.model.observation.Observation):
            super().create(entity)
        else:
            # entity is probably a data array
            url = self.service.url.copy()
            url.path.add(self.CREATE_OBSERVATIONS)
            logging.debug('Posting to ' + str(url.url))
            json_dict = transform_entity_to_json_dict(entity.value)
            try:
                response = self.service.execute('post', url, json=json_dict)
            except requests.exceptions.HTTPError as e:
                error_json = e.response.json()
                error_message = error_json['message']
                logging.error("Creating {} failed with status-code {}, {}".format("Data Array",
                                                                              e.response.status_code,
                                                                              error_message))
            response_text_as_list = json.loads(response.text)
            result = [frost_sta_client.model.observation.Observation(self_link=link) for link in response_text_as_list]
            return result
