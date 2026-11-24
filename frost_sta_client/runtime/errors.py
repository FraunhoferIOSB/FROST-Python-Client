"""HTTP error reporting.

The log line names the failed operation, the status code, and a message taken
from JSON ``message``, otherwise JSON ``error``, otherwise the response text.
The original HTTPError is raised again.
"""

import logging

import requests

logger = logging.getLogger("frost_sta_client")


def handle_server_error(error, failed_action):
    response = getattr(error, "response", None)
    status = getattr(response, "status_code", "unknown")
    error_message = _error_message(error, response)
    logger.error("%s failed with status-code %s, %s", failed_action, status, error_message)
    raise error


def call(service, method, url, failed_action, **kwargs):
    try:
        return service.execute(method, url, **kwargs)
    except requests.HTTPError as error:
        handle_server_error(error, failed_action)


def response_json(response):
    try:
        return response.json()
    except ValueError as exc:
        raise ValueError("Cannot find json in http response") from exc


def _error_message(error, response):
    if response is None:
        return str(error)
    try:
        body = response.json()
    except Exception:
        return getattr(response, "text", str(error))
    if isinstance(body, dict):
        if body.get("message"):
            return body.get("message")
        if body.get("error"):
            return body.get("error")
        return str(body)
    return str(body)
