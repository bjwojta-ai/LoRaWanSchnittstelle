"""REST API routes for the LoRaWAN interface."""
from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.lorawan import client as lorawan_client
from app.lorawan.mqtt_listener import get_recent_uplinks
from app.models import Device, DeviceList, UplinkList

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["LoRaWAN"])


@router.get("/devices", response_model=DeviceList, summary="List all devices")
async def list_devices(app_id: str | None = Query(default=None, description="Application ID (overrides config)")):
    """Return all end devices registered in the LoRaWAN application."""
    try:
        return await lorawan_client.get_devices(app_id)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail=f"LoRaWAN server unreachable: {exc}") from exc


@router.get("/devices/{device_id}", response_model=Device, summary="Get a single device")
async def get_device(
    device_id: str,
    app_id: str | None = Query(default=None, description="Application ID (overrides config)"),
):
    """Return details for a specific end device."""
    try:
        return await lorawan_client.get_device(device_id, app_id)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail=f"LoRaWAN server unreachable: {exc}") from exc


@router.get("/devices/{device_id}/uplinks", response_model=UplinkList, summary="Get stored uplinks for a device")
async def get_device_uplinks(
    device_id: str,
    app_id: str | None = Query(default=None, description="Application ID (overrides config)"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of messages to return"),
):
    """Return the most recent uplink messages stored in the TTN storage integration."""
    try:
        return await lorawan_client.get_uplinks(device_id, app_id, limit)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail=f"LoRaWAN server unreachable: {exc}") from exc


@router.get("/uplinks/live", response_model=UplinkList, summary="Get live uplinks from MQTT buffer")
async def get_live_uplinks(
    limit: int = Query(default=20, ge=1, le=500, description="Maximum number of messages to return"),
):
    """Return the most recent uplink messages received in real-time via MQTT."""
    messages = get_recent_uplinks(limit)
    return UplinkList(messages=messages, total=len(messages))
