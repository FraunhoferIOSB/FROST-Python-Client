import pytest
import subprocess
import time
import requests
import os

from frost_sta_client.service.sensorthingsservice import SensorThingsService
from frost_sta_client.service.auth_handler import AuthHandler

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
