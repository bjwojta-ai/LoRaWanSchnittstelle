"""LoRaWAN client for The Things Network v3 HTTP API."""
from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from app.config import settings
from app.models import Device, DeviceList, UplinkList, UplinkMessage

logger = logging.getLogger(__name__)


def _build_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {settings.ttn_api_key}", "Accept": "application/json"}


def _base_url() -> str:
    return f"{settings.ttn_base_url}/api/v3"


def _parse_device(raw: dict[str, Any], app_id: str) -> Device:
    ids = raw.get("ids", {})
    return Device(
        device_id=ids.get("device_id", ""),
        application_id=app_id,
        name=raw.get("name"),
        description=raw.get("description"),
        dev_eui=ids.get("dev_eui"),
        join_eui=ids.get("join_eui"),
        created_at=raw.get("created_at"),
        updated_at=raw.get("updated_at"),
    )


def _parse_uplink(raw: dict[str, Any]) -> UplinkMessage:
    end_device_ids = raw.get("end_device_ids", {})
    uplink_message = raw.get("uplink_message", {})
    rx_metadata = uplink_message.get("rx_metadata", [{}])
    first_rx = rx_metadata[0] if rx_metadata else {}
    settings_raw = uplink_message.get("settings", {})
    dr = settings_raw.get("data_rate", {}).get("lora", {})

    return UplinkMessage(
        device_id=end_device_ids.get("device_id", ""),
        application_id=end_device_ids.get("application_ids", {}).get("application_id", ""),
        received_at=raw.get("received_at") or uplink_message.get("received_at", "1970-01-01T00:00:00Z"),
        f_cnt=uplink_message.get("f_cnt"),
        f_port=uplink_message.get("f_port"),
        payload_raw=uplink_message.get("frm_payload"),
        payload_decoded=uplink_message.get("decoded_payload"),
        rssi=first_rx.get("rssi"),
        snr=first_rx.get("snr"),
        frequency=settings_raw.get("frequency"),
        spreading_factor=dr.get("spreading_factor"),
        bandwidth=dr.get("bandwidth"),
        gateway_id=first_rx.get("gateway_ids", {}).get("gateway_id"),
    )


async def get_devices(app_id: str | None = None) -> DeviceList:
    """Retrieve all end devices for an application from TTN."""
    application_id = app_id or settings.ttn_app_id
    url = f"{_base_url()}/applications/{application_id}/devices"
    params = {
        "field_mask.paths": [
            "ids",
            "name",
            "description",
            "created_at",
            "updated_at",
        ]
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=_build_headers(), params=params, timeout=10.0)
        response.raise_for_status()
        data = response.json()

    raw_devices: list[dict[str, Any]] = data.get("end_devices", [])
    devices = [_parse_device(d, application_id) for d in raw_devices]
    return DeviceList(devices=devices, total=len(devices))


async def get_device(device_id: str, app_id: str | None = None) -> Device:
    """Retrieve a single end device from TTN."""
    application_id = app_id or settings.ttn_app_id
    url = f"{_base_url()}/applications/{application_id}/devices/{device_id}"
    params = {
        "field_mask.paths": [
            "ids",
            "name",
            "description",
            "created_at",
            "updated_at",
        ]
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=_build_headers(), params=params, timeout=10.0)
        response.raise_for_status()
        data = response.json()

    return _parse_device(data, application_id)


async def get_uplinks(device_id: str, app_id: str | None = None, limit: int = 20) -> UplinkList:
    """Retrieve stored uplink messages for a device from TTN."""
    application_id = app_id or settings.ttn_app_id
    url = f"{_base_url()}/as/applications/{application_id}/packages/storage/uplink_message"
    params = {
        "end_device_ids.device_id": device_id,
        "limit": limit,
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=_build_headers(), params=params, timeout=10.0)
        response.raise_for_status()

        # TTN storage integration returns newline-delimited JSON objects
        messages: list[UplinkMessage] = []
        for line in response.text.splitlines():
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            result = obj.get("result", obj)
            messages.append(_parse_uplink(result))

    return UplinkList(messages=messages, total=len(messages))
