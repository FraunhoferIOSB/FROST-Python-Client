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

import time

from requests.auth import AuthBase
from keycloak import KeycloakOpenID

from frost_sta_client.service.auth_handler import AuthHandler


class KeycloakAuthHandler(AuthHandler):
    def __init__(
        self,
        server_url: str,
        realm_name: str,
        client_id: str,
        username: str,
        password: str,
        timeout: int = 60,
        refresh_skew_seconds: int = 60,
    ):
        """
        Keycloak auth handler based on python-keycloak.

        :param server_url: base url of the Keycloak server (e.g. https://keycloak.example.com/)
        :param realm_name: realm
        :param client_id: client id
        :param username: username used for the password grant
        :param password: password used for the password grant
        :param timeout: request timeout
        :param refresh_skew_seconds: buffer before a token is treated as expiring
        """
        self.refresh_skew_seconds = refresh_skew_seconds
        self._username = username
        self._password = password

        self._oidc = KeycloakOpenID(
            server_url=server_url,
            realm_name=realm_name,
            client_id=client_id,
            timeout=timeout,
        )

        self._token: dict | None = None
        self._token_expires_at: float = 0.0

    def _get_token(self) -> dict:
        """
        Fetches a new token if the current one is expired or about to expire.
        """
        now = time.time()
        if self._token is None or now >= self._token_expires_at:
            token = self._oidc.token(self._username, self._password)

            self._token = token
            expires_in = int(token.get("expires_in", 3600))
            self._token_expires_at = now + expires_in - self.refresh_skew_seconds

        return self._token

    def add_auth_header(self):
        """
        Returns a requests AuthBase (BearerAuth) that sets the access token as
        the Authorization header.
        """
        token = self._get_token()
        return BearerAuth(token["access_token"])


class BearerAuth(AuthBase):
    """Simple bearer auth class for requests."""

    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers['Authorization'] = f'Bearer {self.token}'
        return r
