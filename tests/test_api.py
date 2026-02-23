"""Tests for the FastAPI routes using mocked LoRaWAN client calls."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import Device, DeviceList, UplinkList, UplinkMessage

_NOW = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

SAMPLE_DEVICE = Device(
    device_id="sensor-01",
    application_id="my-app",
    name="Temperatursensor",
    dev_eui="0102030405060708",
)

SAMPLE_UPLINK = UplinkMessage(
    device_id="sensor-01",
    application_id="my-app",
    received_at=_NOW,
    f_cnt=42,
    f_port=1,
    payload_raw="AQID",
    payload_decoded={"temperature": 22.5, "humidity": 60},
    rssi=-85,
    snr=7.5,
    spreading_factor=7,
    bandwidth=125000,
    gateway_id="gw-001",
)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "LoRaWAN" in response.json()["message"]


def test_list_devices(client):
    device_list = DeviceList(devices=[SAMPLE_DEVICE], total=1)
    with patch("app.api.routes.lorawan_client.get_devices", new_callable=AsyncMock, return_value=device_list):
        response = client.get("/api/v1/devices")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["devices"][0]["device_id"] == "sensor-01"
    assert data["devices"][0]["name"] == "Temperatursensor"


def test_list_devices_with_app_id(client):
    device_list = DeviceList(devices=[], total=0)
    with patch("app.api.routes.lorawan_client.get_devices", new_callable=AsyncMock, return_value=device_list) as mock:
        response = client.get("/api/v1/devices?app_id=other-app")
    assert response.status_code == 200
    mock.assert_awaited_once_with("other-app")


def test_get_device(client):
    with patch("app.api.routes.lorawan_client.get_device", new_callable=AsyncMock, return_value=SAMPLE_DEVICE):
        response = client.get("/api/v1/devices/sensor-01")
    assert response.status_code == 200
    data = response.json()
    assert data["device_id"] == "sensor-01"
    assert data["dev_eui"] == "0102030405060708"


def test_get_device_uplinks(client):
    uplink_list = UplinkList(messages=[SAMPLE_UPLINK], total=1)
    with patch("app.api.routes.lorawan_client.get_uplinks", new_callable=AsyncMock, return_value=uplink_list):
        response = client.get("/api/v1/devices/sensor-01/uplinks")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    msg = data["messages"][0]
    assert msg["device_id"] == "sensor-01"
    assert msg["payload_decoded"]["temperature"] == 22.5
    assert msg["rssi"] == -85


def test_get_device_uplinks_limit(client):
    uplink_list = UplinkList(messages=[], total=0)
    with patch("app.api.routes.lorawan_client.get_uplinks", new_callable=AsyncMock, return_value=uplink_list) as mock:
        response = client.get("/api/v1/devices/sensor-01/uplinks?limit=5")
    assert response.status_code == 200
    mock.assert_awaited_once_with("sensor-01", None, 5)


def test_get_live_uplinks(client):
    with patch("app.api.routes.get_recent_uplinks", return_value=[SAMPLE_UPLINK]):
        response = client.get("/api/v1/uplinks/live")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["messages"][0]["device_id"] == "sensor-01"


def test_get_live_uplinks_limit(client):
    with patch("app.api.routes.get_recent_uplinks", return_value=[]) as mock:
        response = client.get("/api/v1/uplinks/live?limit=10")
    assert response.status_code == 200
    mock.assert_called_once_with(10)


def test_list_devices_http_error(client):
    import httpx

    with patch(
        "app.api.routes.lorawan_client.get_devices",
        new_callable=AsyncMock,
        side_effect=httpx.HTTPStatusError(
            "Unauthorized",
            request=httpx.Request("GET", "http://test"),
            response=httpx.Response(401, text="Unauthorized"),
        ),
    ):
        response = client.get("/api/v1/devices")
    assert response.status_code == 401


def test_list_devices_connection_error(client):
    import httpx

    with patch(
        "app.api.routes.lorawan_client.get_devices",
        new_callable=AsyncMock,
        side_effect=httpx.ConnectError("Connection refused"),
    ):
        response = client.get("/api/v1/devices")
    assert response.status_code == 503
