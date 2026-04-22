"""Pytest fixtures for WireMock-backed tests of the LM Studio node.

Assumes a WireMock server is already running (locally or in CI). Set
WIREMOCK_URL to override the default http://127.0.0.1:8089.
"""
import os
import pytest
import requests
from wiremock.client import Mappings
from wiremock.constants import Config


WIREMOCK_URL = os.environ.get("WIREMOCK_URL", "http://127.0.0.1:8089")


@pytest.fixture(scope="session", autouse=True)
def _wiremock_admin():
    Config.base_url = f"{WIREMOCK_URL}/__admin"
    try:
        requests.get(f"{WIREMOCK_URL}/__admin/mappings", timeout=2).raise_for_status()
    except Exception as e:
        pytest.skip(f"WireMock not reachable at {WIREMOCK_URL}: {e}")
    yield


@pytest.fixture(autouse=True)
def _reset_mappings():
    Mappings.delete_all_mappings()
    requests.post(f"{WIREMOCK_URL}/__admin/requests/reset", timeout=2)
    yield


@pytest.fixture
def server_address():
    return WIREMOCK_URL


@pytest.fixture
def node():
    from node import LMStudioNode
    return LMStudioNode()
