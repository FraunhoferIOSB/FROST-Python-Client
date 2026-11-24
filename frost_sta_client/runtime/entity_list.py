"""A page of entities, with optional following of the next link."""

from frost_sta_client.runtime.errors import call, response_json


class EntityList:
    """Loaded entities of one page, plus the link to the next page.

    Iteration follows ``next_link``. ``entities`` and ``get`` stay on the page
    that is already loaded. Assigning an EntityList reads ``entities`` and does
    not iterate, so it does not request the next page.
    """

    def __init__(self, entity_class=None, entities=None):
        self.entity_class = entity_class
        self.entities = list(entities or [])
        self.next_link = None
        self.count = None
        self.navigation_link = None
        self.service = None
        self.callback = None
        self.step_size = None

    def set_service(self, service, _seen=None):
        self.service = service
        for entity in self.entities:
            entity.set_service(service, _seen)

    def arm(self, callback, step_size):
        validate_callback(callback, step_size)
        self.callback = callback
        self.step_size = step_size

    def get(self, index):
        """Return an entity from the loaded page only."""
        if isinstance(index, bool) or not isinstance(index, int):
            raise TypeError("index must be an integer")
        if index < 0:
            raise ValueError("index must be zero or positive")
        return self.entities[index]

    def __iter__(self):
        validate_callback(self.callback, self.step_size)
        index = 0
        page = self
        while True:
            for entity in page.entities:
                if self.callback is not None and index % self.step_size == 0:
                    self.callback(index)
                yield entity
                index += 1
            if not page.next_link:
                return
            page = self._fetch(page.next_link)

    def __len__(self):
        return len(self.entities)

    def _fetch(self, link):
        if self.service is None:
            raise ValueError("service is not set")
        name = self.entity_class.__name__ if self.entity_class is not None else "entities"
        response = call(self.service, "get", link, "Querying {}".format(name))
        payload = response_json(response)
        return entity_list_from_json(payload, self.entity_class, self.service)


def validate_callback(callback, step_size):
    if callback is None and step_size is None:
        return
    if callback is not None and not callable(callback):
        raise TypeError("callback must be callable")
    if callback is None or step_size is None:
        raise TypeError("callback and step_size must both be provided")
    if isinstance(step_size, bool) or not isinstance(step_size, int) or step_size <= 0:
        raise ValueError("step_size must be a positive integer")


def entity_list_from_json(payload, entity_class, service):
    if isinstance(payload, list):
        items = payload
        next_link = None
        count = None
    elif isinstance(payload, dict):
        items = payload.get("value", [])
        if not isinstance(items, list):
            raise ValueError("Cannot find json in http response")
        next_link = payload.get("@iot.nextLink")
        if next_link is None:
            next_link = payload.get("@odata.nextLink")
        if next_link is None:
            next_link = payload.get("@nextLink")
        if "@iot.count" in payload:
            count = payload.get("@iot.count")
        elif "@odata.count" in payload:
            count = payload.get("@odata.count")
        elif "@count" in payload:
            count = payload.get("@count")
        else:
            count = None
    else:
        raise ValueError("Cannot find json in http response")
    entities = [entity_class.from_json(item, service) for item in items]
    listing = EntityList(entity_class=entity_class, entities=entities)
    listing.next_link = next_link
    listing.count = count
    listing.set_service(service)
    return listing
