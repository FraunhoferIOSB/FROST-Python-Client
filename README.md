# frost_sta_client

`frost_sta_client` is a Python client for an [OData 4](https://www.odata.org/) service. You give it one service root, the URL of that API. It reads and writes the entities that root describes.

The package includes a model for the OGC SensorThings API, the interface for sensor observations implemented by [FROST-Server](https://github.com/FraunhoferIOSB/FROST-Server). With that model, `SensorThingsService(url)` already provides `things()`, `locations()`, and the other entity sets listed below. For any other OData service, generate classes from that service's own `$metadata` and construct the service with those classes.

## Install

From a checkout of this repository:

```bash
pip install .
```

That installs the package, the `requests` and `geojson` dependencies, and the `frost-client` command.

## Point the client at a service root

`SensorThingsService` takes the service root and an optional model location. Empty means a built-in SensorThings model. The second argument, `extensions`, is `(multi_datastream, data_array)`. It selects which of the four built-in combinations to load. The default is `(True, True)`, so MultiDatastream and the Data Array action `CreateObservations` are both included. `(True, False)`, `(False, True)`, and `(False, False)` are valid too. `extensions` applies only when the model location is empty. Pass a path with `model`, or a module from `load_model`. That model is used as it stands.

```python
import frost_sta_client as fsc

service = fsc.SensorThingsService("http://localhost:8080/FROST-Server/v1.1")
without_data_array = fsc.SensorThingsService(
    "http://localhost:8080/FROST-Server/v1.1",
    (True, False),
)
from_a_file = fsc.SensorThingsService(
    "http://localhost:8080/FROST-Server/ODATA_4.01",
    model="my_model",
)
```

Before the first read or write, the client reads that root once and keeps the dialect:

- A SensorThings service document, a list of `{name, url}` and no CSDL, writes `@iot.id` and `@iot.selfLink`. A reference uses the primary key.
- `OData-Version: 4.01` writes `@id`. A navigation link is read from `Nav@navigationLink`. A reference uses the entity URL.
- Any other OData response writes `@odata.*`. A reference uses the entity URL.

The loaded model is then compared with the service. It does not matter whether the model was the default or was passed in.

- OData: types, entity sets, and actions are compared with that root's `$metadata`. A mismatch raises `RuntimeError`.
- SensorThings: `serverSettings.conformance` selects the built-in model that is expected. Data Array is `http://www.opengis.net/spec/iot_sensing/1.1/req/data-array/data-array`. MultiDatastream is `http://www.opengis.net/spec/iot_sensing/1.1/req/multi-datastream`. The loaded model is compared with that built-in model. A mismatch raises `RuntimeError`. `/v1.1` is not asked for `$metadata`.

On FROST-Server 2.8.2 the OData `$metadata` documents do not contain `CreateObservations`. The default model includes that action, so constructing the client with an OData root and then reading or writing raises. Use `(True, False)` for MultiDatastream without Data Array, or `open` so the model is that root's `$metadata`. `/v1.1` publishes the data-array conformance and has no `$metadata`.

The client follows the loaded model. It does not suppress `CreateObservations` because a live document omitted the action. When the loaded model contains the action, the call is sent.

For HTTP basic authentication, pass an `AuthHandler`. Omit it when the server does not require authentication.

```python
auth = fsc.AuthHandler(username="read", password="read")
service = fsc.SensorThingsService(
    "http://localhost:8080/FROST-Server/v1.1",
    auth_handler=auth,
)
```

`frost_server/docker-compose.yaml` starts FROST-Server 2.8.2 with OData enabled:

```bash
docker compose -f frost_server/docker-compose.yaml up
```

That server publishes three roots:

| Root | Role |
| --- | --- |
| `http://localhost:8080/FROST-Server/v1.1` | SensorThings. This release does not publish `$metadata` here. |
| `http://localhost:8080/FROST-Server/ODATA_4.0` | The same entities as OData 4.0. `$metadata` is CSDL, and the response header is `OData-Version: 4.0`. |
| `http://localhost:8080/FROST-Server/ODATA_4.01` | The same entities as OData 4.01. `$metadata` is CSDL, and the response header is `OData-Version: 4.01`. |

Basic authentication on that server accepts `read` / `read` for reads and `admin` / `admin` for writes.

With the default extensions, these methods are available: `things`, `locations`, `historical_locations`, `datastreams`, `multi_datastreams`, `sensors`, `observed_properties`, `observations`, `features_of_interest`, and `create_observations`. Turning MultiDatastream off removes `multi_datastreams`. Turning Data Array off removes `create_observations`.

## Generate classes from `$metadata`

Generation reads `$metadata` of the service root you name and writes a Python package. That URL is the only root that is read. The package contains the types, entity sets, navigations, enums, and actions from that document. A service constructed with the package calls those classes.

`generate` and `SensorThingsService.open` require a root that returns a CSDL document at `$metadata`. On FROST-Server 2.8.2, use `/ODATA_4.01` or `/ODATA_4.0`. `/v1.1` has no `$metadata`, so both calls fail for that URL. The included SensorThings model can still be used with `/v1.1` through the constructor above.

### The generate command

```bash
python -m frost_sta_client.generate \
  --url http://localhost:8080/FROST-Server/ODATA_4.01 \
  --username read \
  --password read \
  --out my_model
```

`frost-client generate` accepts the same arguments. `--username` and `--password` are the basic-auth credentials for this download. `--xml path/to/metadata.xml` reads a local CSDL file instead of `--url`. `--out` is the directory that receives `model.py`.

Load that directory and pass it as `model`. Later calls use the same `auth_handler`, because the credentials on the command line are only for the download.

```python
from frost_sta_client.runtime.loader import load_model

model = load_model("my_model")
service = fsc.SensorThingsService(
    "http://localhost:8080/FROST-Server/ODATA_4.01",
    model=model,
    auth_handler=auth,
)
```

`load_model` accepts the directory or the path of its `model.py`. Each entity set in the document becomes a snake_case method on the service. An entity set named `Things` is `service.things()`. The generated classes are attributes of `model`.

### SensorThingsService.open

`open` downloads `$metadata`, writes the package, loads it, and returns a service that uses it. The auth handler is kept on that service.

```python
service = fsc.SensorThingsService.open(
    "http://localhost:8080/FROST-Server/ODATA_4.01",
    "my_model",
    auth_handler=auth,
)
```

`service.model` is the generated module. `service.things().entity_class` is the `Thing` class written for this root.

## A first call

This reads five things from a SensorThings root. In the included model, a Thing has an `id`, a `name`, and a `description`.

```python
import frost_sta_client as fsc

auth = fsc.AuthHandler(username="read", password="read")
service = fsc.SensorThingsService(
    "http://localhost:8080/FROST-Server/v1.1",
    auth_handler=auth,
)
for thing in service.things().query().orderby("name").top(5).list():
    print(thing.id, thing.name)
```

`orderby("name")` sorts ascending. Add `"desc"` for descending order. `top(5)` requests five entities. Walking the result follows a next link when the server sends one. The `.entities` attribute is the current page only.

To create a thing, use an account that can write, then read it back by its key:

```python
auth = fsc.AuthHandler(username="admin", password="admin")
service = fsc.SensorThingsService(
    "http://localhost:8080/FROST-Server/v1.1",
    auth_handler=auth,
)
thing = fsc.Thing(name="buoy", description="harbor buoy")
service.create(thing)
print(service.things().find(thing.id).name)
```

After `open`, build the entity with the class that root's metadata produced:

```python
service = fsc.SensorThingsService.open(
    "http://localhost:8080/FROST-Server/ODATA_4.01",
    "my_model",
    auth_handler=fsc.AuthHandler(username="admin", password="admin"),
)
Thing = service.things().entity_class
thing = Thing(name="buoy", description="harbor buoy")
service.create(thing)
print(service.things().find(thing.id).name)
```

`service.invoke(name, body)` calls an action that the loaded model contains. The client does not refuse the call because a live document omitted the action. When the loaded model has no such action, `invoke` raises `RuntimeError` before any request. A model that does not match the service also raises before the call.

## Which control fields are written

The root read above selects the control fields. They stay cached for later calls.

- `OData-Version: 4.01` writes `@id` for an entity URL. A navigation link is the navigation name plus `@navigationLink`, for example `Locations@navigationLink`.
- Any other OData response writes `@odata.id` and the other `@odata.*` fields.
- A SensorThings service document writes `@iot.id` and `@iot.selfLink`.

`@id` and `@odata.id` carry the entity URL, and so does a reference. `@iot.id` carries the key, and a reference uses that key. `@iot.selfLink` carries the entity URL. When a response has no `@iot.id`, the key is the key property declared for that type.

## OData types in Python (2.0.0)

This table is the mapping in the current release, 2.0.0. The package version is `2.0.0`. A value is stored as the Python type for its OData type. `None` is left out of the JSON. An empty string and an empty object are written. An empty collection is left out.

| OData type | Python in 2.0.0 |
| --- | --- |
| Edm.String | str |
| Edm.Int16, Edm.Int32, Edm.Int64 | int |
| Edm.Boolean | bool |
| Edm.Double, Edm.Decimal, Edm.Single | int or float |
| Edm.DateTimeOffset | timezone-aware datetime.datetime. Two ISO spellings of the same instant are equal. Writing sends one UTC form ending in Z |
| Edm.Date | datetime.date. Writing sends YYYY-MM-DD |
| Edm.TimeOfDay | datetime.time. Writing sends HH:MM:SS, with a fraction only when it is not zero |
| Edm.Duration | datetime.timedelta. Writing sends one ISO-8601 duration, such as PT1H30M |
| An Edm.String property named phenomenonTime, resultTime, validTime, time, or creationTime | a timezone-aware datetime, or a pair of them when the value is an interval. Writing sends one ISO instant, or start/end |
| TM_Object, TM_Period | the generated complex classes `TM_Object` and `TM_Period`. `start` and `end` are a pair of timezone-aware datetimes, written in that UTC form |
| Edm.Geography and Edm.Geometry, including Point, LineString, Polygon, MultiPoint, MultiLineString, MultiPolygon, and GeometryCollection | geojson.Point, geojson.LineString, geojson.Polygon, geojson.MultiPoint, geojson.MultiLineString, geojson.MultiPolygon, geojson.GeometryCollection |
| Collection(T) | list. String, enum, complex, geometry, and time elements are converted; other elements are kept |
| A navigation that returns many entities | EntityList |
| Complex types, including UnitOfMeasurement and Object | the generated complex class. `Object` is the open complex |
| Enumeration | enum.Enum, through `RegisteredEnum`. Writing sends `member.value` |
| Key | int for Edm.Int16, Edm.Int32, and Edm.Int64; str for Edm.String and Edm.Guid; tuple when the key has several properties |
| Null | None. An explicit null on a property with Nullable=false raises ValueError. A missing field stays None |
| Edm.Untyped | the JSON value. A GeoJSON object on a property whose encoding type is geo+json becomes one of the geojson classes above |
| Edm.Binary, Edm.Stream, Edm.Byte, Edm.SByte, and Edm.Guid used as a property | the JSON value is kept |

## Changes from 1.1.53 to 2.0.0

This release is 2.0.0. The table shows where 1.1.53 differs, with 1.1.53 in one column and 2.0.0 in the other.

| | 1.1.53 | 2.0.0 |
| --- | --- | --- |
| `''` and `{}` | Left out of the JSON | Written |
| Equality | A missing key matches a present key. Each class compares only some of its fields. | Every structural field is compared, including when both keys match. A key on only one side makes the two unequal. |
| CreateObservations | `observations().create` posts a data array to CreateObservations | `service.invoke("CreateObservations", body)` sends the call when the loaded model contains the action. The client does not suppress it at runtime. A model that does not match the service raises before the call. |
| Classes | Handwritten classes are imported from the package | Classes are generated from `$metadata` before the program runs, with the generate command or `SensorThingsService.open`. The included SensorThings model is already generated. |
| Edm.Int16, Edm.Int32, Edm.Int64 | `Entity.id` is int or str. There is no general integer mapping. | int |
| Edm.Boolean | No mapping | bool |
| Edm.Double, Edm.Decimal, Edm.Single | No mapping | int or float |
| Edm.DateTimeOffset, Edm.Date, Edm.TimeOfDay, Edm.Duration, and the SensorThings time properties | str, `datetime.datetime`, or list. `utils.check_datetime` keeps the value that was passed. | A timezone-aware datetime, datetime.date, datetime.time, or datetime.timedelta. Equality compares those values, so two ISO spellings of the same instant are equal. Writing sends one fixed ISO form. An interval's start and end are a pair of those values. |
| TM_Object, TM_Period | No complex class. The datetime helper above is used. | Complex classes `TM_Object` and `TM_Period`. `start` and `end` are timezone-aware datetimes. |
| Edm.Geography, Edm.Geometry | A Location's JSON stays a dict, or any `geojson.geometry` class is kept. `process_area` produces Point, LineString, Polygon, or Geometry. | geojson.Point, LineString, Polygon, MultiPoint, MultiLineString, MultiPolygon, GeometryCollection |
| Collection | list of str, or list of `UnitOfMeasurement` | list. String, enum, complex, geometry, and time elements are converted. |
| Object | `properties` and `parameters` are dict | Complex class `Object` |
| Enumeration | No metadata enumeration. Only `DataArrayValue.Property` is defined. | `enum.Enum` through `RegisteredEnum`. Writing sends `member.value`. |
| Key | int or str | int, str, or tuple. Edm.Guid is str. A key of several properties is a tuple. |
| Null | None | None. Nullable=false raises ValueError for an explicit null. A missing field stays None. |
| Edm.Untyped | The JSON value, including result, resultQuality, metadata, and feature | The JSON value. A geo+json object becomes a geojson geometry. |
