import os
import importlib.util
from pathlib import Path
import pytest

from frost_sta_client.odata_codegen.parser import parse_metadata
from frost_sta_client.odata_codegen.generator import generate_from_metadata
from frost_sta_client.odata_codegen.runtime import find_odata_endpoint
from frost_sta_client.cli import main as cli_main

SAMPLE_METADATA = """<?xml version=\"1.0\" encoding=\"utf-8\"?>
<edmx:Edmx Version=\"4.01\" xmlns:edmx=\"http://docs.oasis-open.org/odata/ns/edmx\">
  <edmx:DataServices>
    <Schema Namespace=\"TestModel\" xmlns=\"http://docs.oasis-open.org/odata/ns/edm\">
      <EntityType Name=\"Location\">
        <Key><PropertyRef Name=\"Id\"/></Key>
        <Property Name=\"Id\" Type=\"Edm.Int32\" Nullable=\"false\"/>
        <Property Name=\"Name\" Type=\"Edm.String\"/>
      </EntityType>
      <EntityType Name=\"Thing\">
        <Key><PropertyRef Name=\"Id\"/></Key>
        <Property Name=\"Id\" Type=\"Edm.Int32\" Nullable=\"false\"/>
        <Property Name=\"Name\" Type=\"Edm.String\"/>
        <NavigationProperty Name=\"Locations\" Type=\"Collection(TestModel.Location)\"/>
      </EntityType>
      <EntityContainer Name=\"Container\">
        <EntitySet Name=\"Things\" EntityType=\"TestModel.Thing\"/>
        <EntitySet Name=\"Locations\" EntityType=\"TestModel.Location\"/>
      </EntityContainer>
    </Schema>
  </edmx:DataServices>
</edmx:Edmx>
"""


def _load_module_from_path(module_path: Path):
    spec = importlib.util.spec_from_file_location(module_path.stem, str(module_path))
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)  # type: ignore
    return mod


def test_parse_and_generate(tmp_path: Path):
    model = parse_metadata(SAMPLE_METADATA)
    assert 'entity_types' in model and 'entity_sets' in model
    out_file = generate_from_metadata(SAMPLE_METADATA, str(tmp_path), module_name='dm', source_url='http://x', odata_version='4.01')
    assert os.path.exists(out_file)
    mod = _load_module_from_path(Path(out_file))
    # Classes must exist
    assert hasattr(mod, 'Thing') and hasattr(mod, 'Location')
    # Instantiate and check attributes (snake_case, Entity-based)
    t = mod.Thing(id=1, name='A')
    l = mod.Location(id=2, name='L')
    assert t.id == 1 and t.name == 'A'
    assert l.id == 2 and l.name == 'L'
    # Navigation attribute exists and defaults to None (EntityList will be used once set from JSON)
    assert hasattr(t, 'locations')
    assert getattr(t, 'locations') is None
    # ENTITY_SETS mapping
    assert isinstance(getattr(mod, 'ENTITY_SETS', {}), dict)
    assert mod.ENTITY_SETS.get('Things') is mod.Thing


def test_find_odata_endpoint_prefers_401_then_40(monkeypatch):
    class R:
        def __init__(self, code, text=''):
            self.status_code = code
            self.text = text

    def fake_get(url, headers=None, auth=None, timeout=None):
        if 'ODATA_4.01' in url:
            return R(404, '')
        if 'ODATA_4.0' in url:
            return R(200, '<edmx:Edmx xmlns:edmx="http://docs.oasis-open.org/odata/ns/edmx"></edmx:Edmx>')
        return R(404, '')

    monkeypatch.setattr('requests.get', fake_get)
    info = find_odata_endpoint('http://example.org/FROST-Server')
    assert info is not None and info['version'] == '4.0'


def test_cli_generates_code(tmp_path: Path, monkeypatch):
    class Resp:
        status_code = 200
        text = SAMPLE_METADATA
        def raise_for_status(self):
            pass

    def fake_get(url, headers=None, auth=None, timeout=None):
        return Resp()

    monkeypatch.setattr('requests.get', fake_get)
    rc = cli_main(['--url', 'http://localhost:8080/FROST-Server', '--out', str(tmp_path), '--module', 'dmgen'])
    assert rc == 0
    out = tmp_path / 'dmgen.py'
    assert out.exists()
