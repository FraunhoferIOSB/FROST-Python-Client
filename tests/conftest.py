import pytest
import subprocess
import time
import requests
import os

from frost_sta_client.service.sensorthingsservice import SensorThingsService
from frost_sta_client.service.auth_handler import AuthHandler


def _server_ready(url):
    auth_handler = AuthHandler(username="read", password="read")
    try:
        response = requests.get(
            url,
            auth=auth_handler.add_auth_header(),
            timeout=3,
        )
    except requests.RequestException:
        return False
    return response.status_code == 200


@pytest.fixture(scope='session')
def frost_server():
    if os.environ.get('FROST_STA_CLIENT_RUN_INTEGRATION') != '1':
        # Skip starting server if not requested
        yield
        return
    started = False
    full = 'http://localhost:8080/FROST-Server/v1.1'
    plain = 'http://localhost:8082/FROST-Server/v1.1'
    if not (_server_ready(full) and _server_ready(plain)):
        # Start FROST-Server using Podman
        subprocess.run(['podman', 'compose', '-f', 'frost_server/docker-compose.yaml', 'up', '-d'])
        started = True
        # Wait for server to start
        for _ in range(40):
            if _server_ready(full) and _server_ready(plain):
                break
            time.sleep(1)
        else:
            raise RuntimeError('FROST-Server failed to start')
    yield
    if started:
        subprocess.run(['podman', 'compose', '-f', 'frost_server/docker-compose.yaml', 'down'])


@pytest.fixture
def sensorthings_service(frost_server):
    url = 'http://localhost:8080/FROST-Server/v1.1'
    auth_handler = AuthHandler(
        username="admin",
        password="admin"
    )
    return SensorThingsService(url, (True, True, True), auth_handler=auth_handler)
