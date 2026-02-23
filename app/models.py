from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class UplinkMessage(BaseModel):
    """A decoded uplink message received from a LoRaWAN device."""

    device_id: str
    application_id: str
    received_at: datetime
    f_cnt: int | None = None
    f_port: int | None = None
    payload_raw: str | None = None  # base64 encoded
    payload_decoded: dict[str, Any] | None = None
    rssi: int | None = None
    snr: float | None = None
    frequency: float | None = None
    spreading_factor: int | None = None
    bandwidth: int | None = None
    gateway_id: str | None = None


class Device(BaseModel):
    """A LoRaWAN device registered in the network server."""

    device_id: str
    application_id: str
    name: str | None = None
    description: str | None = None
    dev_eui: str | None = None
    join_eui: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class DeviceList(BaseModel):
    """Paginated list of devices."""

    devices: list[Device]
    total: int


class UplinkList(BaseModel):
    """List of uplink messages."""

    messages: list[UplinkMessage]
    total: int


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str
