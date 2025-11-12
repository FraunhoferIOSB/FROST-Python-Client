from __future__ import annotations

from typing import Any, Optional, List, Dict

# Generic OData DAO for code-generated models.
# It uses the code-generated module's ENTITY_SETS mapping to build URLs and (de)serialize entities.

class GenericODataDao:
    def __init__(self, service, entity_set: str, model_module: Any):
        self.service = service
        self.entity_set = entity_set
        self.model_module = model_module

    def _base_collection_url(self) -> str:
        base = self.service.url.url
        if not str(self.service.url.path).endswith('/'):
            base += '/'
        return base + self.entity_set

    def _entity_url(self, entity_id: Any) -> str:
        if isinstance(entity_id, str):
            _id = f"'{entity_id}'"
        else:
            _id = entity_id
        return f"{self._base_collection_url()}({_id})"

    def create(self, entity: Any) -> None:
        # POST to collection; deep inserts are supported if server allows them.
        payload = entity.__getstate__()
        resp = self.service.execute('POST', self._base_collection_url(), json=payload)
        try:
            data = resp.json()
        except Exception:
            data = None
        if isinstance(data, dict):
            try:
                entity.__setstate__(data)
            except Exception:
                # Keep entity as-is if server returns minimal response
                pass
        # ensure service propagation for nested entities
        try:
            entity.set_service(self.service)
            entity.ensure_service_on_children(self.service)
        except Exception:
            pass

    def update(self, entity: Any) -> None:
        if getattr(entity, 'id', None) is None:
            raise ValueError('Cannot update an entity without id')
        payload = entity.__getstate__()
        self.service.execute('PATCH', self._entity_url(entity.id), json=payload)

    def patch(self, entity: Any, patches: List[Dict[str, Any]]) -> None:
        if getattr(entity, 'id', None) is None:
            raise ValueError('Cannot patch an entity without id')
        headers = {'Content-Type': 'application/json-patch+json'}
        self.service.execute('PATCH', self._entity_url(entity.id), headers=headers, json=patches)

    def delete(self, entity: Any) -> None:
        if getattr(entity, 'id', None) is None:
            raise ValueError('Cannot delete an entity without id')
        self.service.execute('DELETE', self._entity_url(entity.id))
