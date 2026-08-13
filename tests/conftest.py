import pytest
import subprocess
import time
import requests
import os

from frost_sta_client.service.sensorthingsservice import SensorThingsService
from frost_sta_client.service.auth_handler import AuthHandler
from frost_sta_client.service.keycloak_auth_handler import KeycloakAuthHandler

import socket

KEYCLOAK_REALM = 'frost-test'
KEYCLOAK_CLIENT_ID = 'frost-server'

@pytest.fixture(scope='session')
def frost_server():
    if os.environ.get('FROST_STA_CLIENT_RUN_INTEGRATION') != '1':
        # Skip starting server if not requested
        yield
        return
    # Start FROST-Server using Podman
    subprocess.run(['podman', 'compose', '-f', 'frost_server/docker-compose.yaml', 'up', '-d'])
    # Wait for server to start
    url = 'http://localhost:8080/FROST-Server'
    for _ in range(30):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                break
        except requests.ConnectionError:
            time.sleep(1)
    else:
        raise RuntimeError('FROST-Server failed to start')
    vrl = 'http://localhost:8080/FROST-Server/v1.1'
    auth_handler = AuthHandler(
        username="read",
        password="read"
    )
    response = requests.get(vrl, auth=auth_handler.add_auth_header())
    if response.status_code == 401:
        raise RuntimeError('Failed to authorize at FROST-Server')
    yield
    subprocess.run(['podman', 'compose', '-f', 'frost_server/docker-compose.yaml', 'down'])

@pytest.fixture
def sensorthings_service(frost_server):
    url = 'http://localhost:8080/FROST-Server/v1.1'
    auth_handler = AuthHandler(
        username="admin",
        password="admin"
    )
    return SensorThingsService(url, auth_handler=auth_handler)


def _external_ip():
    """The host's own LAN IP. Keycloak and FROST are addressed through it so the token
    issuer is the same whether the token is minted here on the host or validated inside
    the FROST container. See tests/keycloak/docker-compose.yaml."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        return s.getsockname()[0]
    finally:
        s.close()


def _keycloak_url(ip):
    return 'http://{}:8180'.format(ip)


def _frost_url(ip):
    return 'http://{}:8090/FROST-Server/v1.1'.format(ip)


def _can_get_token(ip):
    """Whether the realm is imported and hands out a token for the read user."""
    try:
        response = requests.post(
            '{}/realms/{}/protocol/openid-connect/token'.format(_keycloak_url(ip), KEYCLOAK_REALM),
            data={
                'grant_type': 'password',
                'client_id': KEYCLOAK_CLIENT_ID,
                'username': 'read',
                'password': 'read',
            },
        )
    except requests.ConnectionError:
        return False
    return response.status_code == 200


@pytest.fixture(scope='session')
def frost_keycloak_server():
    if os.environ.get('FROST_STA_CLIENT_RUN_INTEGRATION') != '1':
        # Skip starting the server if not requested
        yield None
        return
    ip = _external_ip()
    env = {**os.environ, 'EXTERNAL_IP': ip}
    compose = ['podman', 'compose', '-f', 'tests/keycloak/docker-compose.yaml']
    subprocess.run(compose + ['up', '-d'], env=env)
    # Wait for Keycloak to have imported the realm and to mint a token
    for _ in range(60):
        if _can_get_token(ip):
            break
        time.sleep(2)
    else:
        subprocess.run(compose + ['down', '-v'], env=env)
        raise RuntimeError('Keycloak failed to start')
    # Wait for FROST to come up. With anonymous read disabled an unauthenticated request is
    # rejected (302 to the Keycloak login, or 401), so any of these means the server is up
    # and enforcing authentication.
    for _ in range(30):
        try:
            response = requests.get(_frost_url(ip), allow_redirects=False)
            if response.status_code in (200, 302, 401):
                break
        except requests.ConnectionError:
            time.sleep(1)
    else:
        subprocess.run(compose + ['down', '-v'], env=env)
        raise RuntimeError('FROST-Server failed to start')
    yield ip
    subprocess.run(compose + ['down', '-v'], env=env)


@pytest.fixture
def keycloak_sensorthings_service(frost_keycloak_server):
    ip = frost_keycloak_server
    auth_handler = KeycloakAuthHandler(
        server_url=_keycloak_url(ip),
        realm_name=KEYCLOAK_REALM,
        client_id=KEYCLOAK_CLIENT_ID,
        username="write",
        password="write",
    )
    return SensorThingsService(_frost_url(ip), auth_handler=auth_handler)
