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


import requests
from requests.adapters import HTTPAdapter, Retry


class SessionHandler:
    """
    Handles the request session management and retries.         

    Attributes:
        total_retries: Total number of retries to allow. Takes precedence over other counts.
        connect: How many connection-related errors to retry on.
        backoff_factor: A backoff factor to apply between attempts after the second try
        status_forcelist: A set of integer HTTP status codes that we should force a retry on
    """
    def __init__(self, total_retries = 20, connect = 15, backoff_factor = 0.3,status_forcelist = [500, 502, 503, 504]):

        self.current_session = None
        self.total_retries =total_retries
        self.connect=connect
        self.backoff_factor = backoff_factor
        self.status_forcelist= status_forcelist
        self.auth = None

    def get_session(self):
        if self.current_session is None:
            self.create_new_session()

        return self.current_session

    def create_new_session(self):
        self.current_session = requests.Session()

        retries = Retry(
            total=self.total_retries,
            connect=self.connect,
            backoff_factor=self.backoff_factor,
            status_forcelist=self.status_forcelist,
        )

        adapter = HTTPAdapter(max_retries=retries)
        self.current_session.mount("http://", adapter)
        self.current_session.mount("https://", adapter)

        if self.auth is not None:
            self.current_session.auth = self.auth


    def close_session(self):
        if self.current_session is not None:
            self.current_session.close()
            self.current_session = None

    def restart_session(self):
        self.close_session()
        self.create_new_session

    def set_auth(self, auth):
        self.auth=auth
        if self.current_session is not None:
            self.current_session.auth=auth
        