"""The generator emits declarations and no per-type behavior."""

import importlib.util
from pathlib import Path

import pytest

from frost_sta_client.generate import render
from frost_sta_client.runtime.csdl import parse_csdl

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "frost_sta_client" / "metadata" / "frost-2.8.2-odata-4.01.csdl.xml"

EXTRA = """<?xml version="1.0" encoding="UTF-8"?>
<edmx:Edmx Version="4.0" xmlns:edmx="http://docs.oasis-open.org/odata/ns/edmx">
  <edmx:DataServices>
    <Schema Namespace="example.extra" xmlns="http://docs.oasis-open.org/odata/ns/edm">
      <EnumType Name="Status">
        <Member Name="On" Value="1"/>
        <Member Name="Off" Value="2"/>
      </EnumType>
      <EntityType Name="BaseThing" Abstract="true">
        <Key><PropertyRef Name="id"/></Key>
        <Property Name="id" Type="Edm.Int64" Nullable="false"/>
        <Property Name="name" Type="Edm.String"/>
      </EntityType>
      <EntityType Name="Widget" BaseType="example.extra.BaseThing">
        <Property Name="Class" Type="Edm.String"/>
        <Property Name="status" Type="example.extra.Status"/>
      </EntityType>
      <Action Name="Ping" IsBound="true">
        <Parameter Name="bindingParameter" Type="example.extra.Widget" Nullable="false"/>
        <Parameter Name="note" Type="Edm.String"/>
        <ReturnType Type="Edm.Boolean"/>
      </Action>
      <Function Name="CountWidgets" IsBound="false">
        <ReturnType Type="Edm.Int32"/>
      </Function>
      <EntityContainer Name="Container">
        <EntitySet Name="Widgets" EntityType="example.extra.Widget"/>
        <ActionImport Name="Ping" Action="example.extra.Ping"/>
        <FunctionImport Name="CountWidgets" Function="example.extra.CountWidgets"/>
      </EntityContainer>
    </Schema>
  </edmx:DataServices>
</edmx:Edmx>
"""


def test_checked_in_model_is_deterministic_and_has_no_per_type_behavior():
    text = FIXTURE.read_text(encoding="utf-8")
    model = parse_csdl(text)
    source = {"service_root": None, "metadata_sha256": "abc"}
    assert render(model, source) == render(model, source)
    generated = (ROOT / "frost_sta_client" / "generated" / "model.py").read_text(encoding="utf-8")
    assert "def __eq__" not in generated
    assert "def __getstate__" not in generated
    assert "def __setstate__" not in generated
    assert "CreateObservations" not in model.actions
    assert ("MultiDatastreams", "de.FROST.MultiDatastream") in model.entity_sets
    assert ("FeaturesOfInterest", "de.FROST.FeatureOfInterest") in model.entity_sets
    location = next(prop for prop in model.type_named("Location").properties if prop.name == "location")
    assert location.edm == "Edm.Geometry"
    data_types = next(
        prop for prop in model.type_named("MultiDatastream").properties
        if prop.name == "multiObservationDataTypes"
    )
    assert data_types.edm == "Collection(Edm.String)"


def test_generator_emits_enums_actions_and_inherited_properties(tmp_path):
    model = parse_csdl(EXTRA)
    assert model.action_bindings["Ping"] is True
    assert model.function_bindings["CountWidgets"] is False
    widget = model.type_named("Widget")
    assert [prop.name for prop in widget.properties] == ["id", "name", "Class", "status"]
    ping = model.action_list[0]
    assert [(param.name, param.edm, param.nullable) for param in ping.parameters] == [
        ("bindingParameter", "example.extra.Widget", False),
        ("note", "Edm.String", True),
    ]
    assert ping.return_type == "Edm.Boolean"
    assert model.function_list[0].return_type == "Edm.Int32"
    files = render(model, {"service_root": "http://example.org/Widgets", "metadata_sha256": "def"})
    out = tmp_path / "model.py"
    out.write_text(files["model.py"], encoding="utf-8")
    assert "def __eq__" not in files["model.py"]
    spec = importlib.util.spec_from_file_location("generated_extra_under_test", out)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.Status.On.value == 1
    item = module.Widget(name="box", class_value="label", status="On")
    assert item.status is module.Status.On
    assert item.to_json(None)["status"] == 1
    names = [prop.python_name for prop in module.Widget.__properties__]
    assert "class_value" in names
    assert "name" in names
    assert module.ACTIONS[0].parameters[1].name == "note"
    assert module.ACTIONS[0].return_type == "Edm.Boolean"
    assert "from .model import" in files["__init__.py"]


COMPOSITE = """<?xml version="1.0" encoding="UTF-8"?>
<edmx:Edmx Version="4.0" xmlns:edmx="http://docs.oasis-open.org/odata/ns/edmx">
  <edmx:DataServices>
    <Schema Namespace="example.extra" xmlns="http://docs.oasis-open.org/odata/ns/edm">
      <EntityType Name="Widget">
        <Key><PropertyRef Name="id"/></Key>
        <Property Name="id" Type="Edm.Int64" Nullable="false"/>
        <Property Name="name" Type="Edm.String"/>
      </EntityType>
      <EntityContainer Name="Left">
        <EntitySet Name="Widgets" EntityType="example.extra.Widget"/>
      </EntityContainer>
    </Schema>
    <Schema Namespace="other.ns" xmlns="http://docs.oasis-open.org/odata/ns/edm">
      <EntityType Name="Widget">
        <Key>
          <PropertyRef Name="tenant"/>
          <PropertyRef Name="code"/>
        </Key>
        <Property Name="tenant" Type="Edm.String" Nullable="false"/>
        <Property Name="code" Type="Edm.Int64" Nullable="false"/>
        <Property Name="label" Type="Edm.String"/>
      </EntityType>
      <EntityContainer Name="Right">
        <EntitySet Name="OtherWidgets" EntityType="other.ns.Widget"/>
      </EntityContainer>
    </Schema>
  </edmx:DataServices>
</edmx:Edmx>
"""


def test_composite_keys_and_duplicate_short_names_load(tmp_path):
    import frost_sta_client as fsc
    from frost_sta_client.runtime.loader import load_model
    from frost_sta_client.runtime.registry import resolve
    from frost_sta_client.runtime.service import SensorThingsService

    model = parse_csdl(COMPOSITE)
    with pytest.raises(KeyError):
        model.type_named("Widget")
    assert model.type_named("other.ns.Widget").keys == ["tenant", "code"]
    files = render(model, {"service_root": "http://example.org/svc", "metadata_sha256": "abc"})
    out = tmp_path / "general"
    out.mkdir()
    (out / "model.py").write_text(files["model.py"], encoding="utf-8")
    (out / "__init__.py").write_text(files["__init__.py"], encoding="utf-8")
    loaded = load_model(out)
    assert loaded.example_extra_Widget is not fsc.Thing
    assert resolve("Widget") is None
    assert resolve("other.ns.Widget") is loaded.other_ns_Widget
    item = loaded.other_ns_Widget(tenant="a", code=2, label="x")
    assert item.id == ("a", 2)
    same = loaded.other_ns_Widget(tenant="a", code=2, label="x")
    assert item == same
    assert item != loaded.other_ns_Widget(tenant="a", code=3, label="x")
    service = SensorThingsService("http://example.org/svc", model=loaded, control="@odata")
    body = item.to_json(service)
    assert body["tenant"] == "a"
    assert body["code"] == 2
    assert body["@odata.id"] == "http://example.org/svc/OtherWidgets(tenant='a',code=2)"
    with pytest.raises(AttributeError):
        service.things
    assert service.other_widgets().entity_class is loaded.other_ns_Widget
