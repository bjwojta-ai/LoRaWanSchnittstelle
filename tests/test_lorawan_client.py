"""Tests for LoRaWAN client parsing helpers."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from app.lorawan.client import _parse_device, _parse_uplink


def test_parse_device_full():
    raw = {
        "ids": {
            "device_id": "sensor-01",
            "dev_eui": "AABBCCDDEEFF0011",
            "join_eui": "1122334455667788",
        },
        "name": "Humidity Sensor",
        "description": "Office humidity",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-10T12:00:00Z",
    }
    device = _parse_device(raw, "my-app")
    assert device.device_id == "sensor-01"
    assert device.application_id == "my-app"
    assert device.name == "Humidity Sensor"
    assert device.dev_eui == "AABBCCDDEEFF0011"
    assert device.join_eui == "1122334455667788"


def test_parse_device_minimal():
    raw = {"ids": {"device_id": "minimal-device"}}
    device = _parse_device(raw, "app-x")
    assert device.device_id == "minimal-device"
    assert device.name is None
    assert device.dev_eui is None


def test_parse_uplink_full():
    raw = {
        "end_device_ids": {
            "device_id": "sensor-01",
            "application_ids": {"application_id": "my-app"},
        },
        "received_at": "2024-01-15T12:00:00Z",
        "uplink_message": {
            "f_cnt": 42,
            "f_port": 1,
            "frm_payload": "AQID",
            "decoded_payload": {"temperature": 22.5},
            "rx_metadata": [
                {
                    "rssi": -85,
                    "snr": 7.5,
                    "gateway_ids": {"gateway_id": "gw-001"},
                }
            ],
            "settings": {
                "frequency": "868100000",
                "data_rate": {
                    "lora": {
                        "spreading_factor": 7,
                        "bandwidth": 125000,
                    }
                },
            },
        },
    }
    uplink = _parse_uplink(raw)
    assert uplink.device_id == "sensor-01"
    assert uplink.application_id == "my-app"
    assert uplink.f_cnt == 42
    assert uplink.f_port == 1
    assert uplink.payload_raw == "AQID"
    assert uplink.payload_decoded == {"temperature": 22.5}
    assert uplink.rssi == -85
    assert uplink.snr == 7.5
    assert uplink.spreading_factor == 7
    assert uplink.bandwidth == 125000
    assert uplink.gateway_id == "gw-001"


def test_parse_uplink_minimal():
    raw = {
        "end_device_ids": {"device_id": "dev-x", "application_ids": {"application_id": "app-x"}},
        "uplink_message": {},
    }
    uplink = _parse_uplink(raw)
    assert uplink.device_id == "dev-x"
    assert uplink.f_cnt is None
    assert uplink.rssi is None
    assert uplink.payload_decoded is None


def test_parse_uplink_no_rx_metadata():
    raw = {
        "end_device_ids": {"device_id": "dev-y", "application_ids": {"application_id": "app-y"}},
        "received_at": "2024-06-01T10:00:00Z",
        "uplink_message": {"rx_metadata": []},
    }
    uplink = _parse_uplink(raw)
    assert uplink.rssi is None
    assert uplink.gateway_id is None
