import os

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get('FROST_STA_CLIENT_RUN_INTEGRATION') != '1',
    reason='Integration tests require a FROST server. Set FROST_STA_CLIENT_RUN_INTEGRATION=1 to run.')

from frost_sta_client.model import thing


def test_keycloak_authenticated_crud(keycloak_sensorthings_service):
    """Happy path: with a Keycloak token the client may create and read a Thing on a
    FROST server that rejects anonymous access."""
    t = thing.Thing(
        name='Keycloak Thing',
        description='created with a keycloak token')
    keycloak_sensorthings_service.create(t)
    assert t.id is not None

    retrieved = keycloak_sensorthings_service.things().find(t.id)
    assert retrieved.name == 'Keycloak Thing'
