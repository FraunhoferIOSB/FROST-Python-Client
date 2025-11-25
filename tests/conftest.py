import pytest
import subprocess
import time
import requests
import os

from frost_sta_client.service.sensorthingsservice import SensorThingsService
from frost_sta_client.service.auth_handler import AuthHandler

# Run code generation and install model wrappers before any tests start
def pytest_sessionstart(session):
    # 1) Generate OData datamodel (falls back to metadata.xml if endpoint unavailable)
    try:
        from frost_sta_client.odata_codegen.generator import generate_from_url
        url = os.environ.get('FROST_STA_CLIENT_CODEGEN_URL', 'http://localhost:8080/FROST-Server')
        username = os.environ.get('FROST_STA_CLIENT_CODEGEN_USER')
        password = os.environ.get('FROST_STA_CLIENT_CODEGEN_PASS')
        auth = (username, (password or '')) if username is not None else None
        generate_from_url(url, 'frost_sta_client/generated/odata', 'datamodel', auth=auth)
    except Exception:
        # Non-fatal: generator handles fallback internally
        pass

    # 2) Generate model wrappers under frost_sta_client/model so imports like frost_sta_client.model.thing work
    try:
        from frost_sta_client.odata_codegen.install_model import ENTITY_FILE_MAP, ensure_dir as _ensure_dir, write_wrapper as _write_wrapper, write_model_init as _write_model_init
        model_dir = os.path.join('frost_sta_client', 'model')
        _ensure_dir(model_dir)
        from frost_sta_client.model.ext.entity_type import EntityTypes
        entities = [k for k in EntityTypes.keys() if ENTITY_FILE_MAP.get(k)]
        for singular in entities:
            relations = EntityTypes[singular].get('relations_list', [])
            _write_wrapper(model_dir, singular, relations)
        _write_model_init(model_dir, entities)
    except Exception:
        # Non-fatal: other unit tests can still proceed
        pass

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
