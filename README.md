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
location = fsc.Location(name="here", description="and there", location=point)
 
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