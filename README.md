# Sensorthings API Python Client

The **FR**aunhofer **O**pensource **S**ensor**T**hings API Python Client is a python package for the [SensorThingsAPI](https://github.com/opengeospatial/sensorthings) and aims to simplify development of SensorThings enabled client applications

## Features
* CRUD operations
* Queries on entity lists
* MultiDatastreams

## API

The `SensorThingsService` class is central to the library. An instance of it represents a SensorThings service and is 
identified by a URI.


### CRUD operations
The source code below demonstrates the CRUD operations for Thing objects. Operations for other entities work similarly.
```
import frost_sta_client as fsc

url = "exampleserver.com/FROST-Server/v1.1"
service = fsc.SensorThingsService(url)
```
#### Creating Entities
```
from geojson import Point

point = Point((-115.81, 37.24))
location = fsc.Location(name="here", description="and there", location=point, encoding_type='application/geo+json')
 
thing = fsc.Thing(name='new thing',
              description='I am a thing with a location',
              properties={'withLocation': True, 'owner': 'IOSB'})
thing.locations = [location]
service.create(thing)
```
#### Querying Entities
Queries to the FROST Server can be modified to include filters, selections or expansions. The return value is always
an EntityList object, containing the parsed json response of the server.
```
things_list = service.things().query().filter('id eq 1').list()

for thing in things_list:
    print("my name is: {}".format(thing.name))
```
### EntityLists

When querying a list of entities that is particularly long, the FROST server divides the list into smaller chunks,
replaying to the request with the first chunk accompanied by the link to the next one.

The class `EntityList` implements the function `__iter__` and `__next__` which makes it capable of iterating 
through the entire list of entities, including the calls to all chunks.
```
things_list = service.things().query().list()

for thing in things_list:
    print("my name is: {}".format(thing.name))
```

In a case where only the current chunk is supposed to be iterated, the `entities` list can be used.

```
things_list = service.things().query().top(20).list()

for thing in things_list.entities:
    print("my name is: {}".format(thing.name))
```

### Queries to related entity lists

For example the Observations of a given Datastream can be queried via
```
datastream = service.datastreams().find(1)
observations_list = datastream.get_observations().query().filter("result gt 10").list()
```

### Callback function in `EntityList`
The progress of the loading process can be tracked by supplying a callback function along with a step size. The callback
function and the step size must both be provided to the `list` function (see example below).

If a callback function and a step size are used, the callback function is called every time the step size is
reached during the iteration within the for-loop. (Note that the callback function so far only works in
combination with a for-loop).

The callback function is called with one argument, which is the current index of the iteration.

```
def callback_func(loaded_entities):
    print("loaded {} entities!".format(loaded_entities))

service = fsc.SensorThingsService('example_url')

things = service.things().query().list(callback=callback_func, step_size=5)
for thing in things:
    print(thing.name)
```

### DataArrays
DataArrays can be used to make the creation of Observations easier, because with an DataArray only one HTTP Request
has to be created.

An example usage looks as follows:
```
    import frost_sta_client as fsc
    
    service = fsc.SensorThingsService("exampleserver.com/FROST-Server/v1.1")
    dav = fsc.model.ext.data_array_value.DataArrayValue()
    datastream = service.datastreams().find(1)
    foi = service.feature_of_interest().find(1)
    components = {dav.Property.PHENOMENON_TIME, dav.Property.RESULT, dav.Property.FEATURE_OF_INTEREST}
    dav.components = components
    dav.datastream = datastream
    obs1 = fsc.Observation(result=3,
                           phenomenon_time='2022-12-19T10:00:00Z',
                           datastream=datastream,
                           feature_of_interest=foi)
    obs2 = fsc.Observation(result=5,
                           phenomenon_time='2022-12-19T17:00:00Z',
                           datastream=datastream,
                           feature_of_interest=foi)
    dav.add_observation(obs1)
    dav.add_observation(obs2)
    dad = fsc.model.ext.data_array_document.DataArrayDocument()
    dad.add_data_array_value(dav)
    result_list = service.observations().create(dad)
```

### Json (De)Serialization
Since not all possible backends that are configurable in jsonpickle handle long floats equally, the backend json
module is set to demjson3 per default. The backend can be modified by calling
`jsonpickle.set_preferred_backend('name_of_preferred_backend')` anywhere in the code that uses the client.