import pytest
import subprocess
import time
import requests

from frost_sta_client.service.sensorthingsservice import SensorThingsService

@pytest.fixture(scope='session')
def frost_server():
    # Start FROST-Server using Podman
    subprocess.run(['podman', 'compose', '-f', 'frost_server/docker-compose.yaml', 'up', '-d'])
    # Wait for server to start
    url = 'http://localhost:8080/FROST-Server/v1.1'
    for _ in range(30):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                break
        except requests.ConnectionError:
            time.sleep(1)
    else:
        raise RuntimeError('FROST-Server failed to start')
    yield
    subprocess.run(['podman', 'compose', '-f', '../frost_server/docker-compose.yaml', 'down'])

@pytest.fixture
def sensorthings_service(frost_server):
    url = 'http://localhost:8080/FROST-Server/v1.1'
    return SensorThingsService(url)
