"""MQTT listener for real-time LoRaWAN uplink messages via The Things Network."""
from __future__ import annotations

import json
import logging
import ssl
import threading
from collections import deque
from datetime import datetime, timezone
from typing import Deque

import paho.mqtt.client as mqtt

from app.config import settings
from app.lorawan.client import _parse_uplink
from app.models import UplinkMessage

logger = logging.getLogger(__name__)

# In-memory ring buffer for the most recent uplinks received via MQTT
_uplink_buffer: Deque[UplinkMessage] = deque(maxlen=500)
_buffer_lock = threading.Lock()

_mqtt_client: mqtt.Client | None = None


def get_recent_uplinks(limit: int = 20) -> list[UplinkMessage]:
    """Return the most recent uplink messages received via MQTT."""
    with _buffer_lock:
        items = list(_uplink_buffer)
    return items[-limit:]


def _on_connect(client: mqtt.Client, userdata: object, flags: dict, rc: int, properties=None) -> None:
    if rc == 0:
        topic = f"v3/{settings.ttn_app_id}@{settings.ttn_tenant_id}/devices/+/up"
        client.subscribe(topic)
        logger.info("MQTT connected; subscribed to %s", topic)
    else:
        logger.error("MQTT connection failed with code %d", rc)


def _on_message(client: mqtt.Client, userdata: object, msg: mqtt.MQTTMessage) -> None:
    try:
        payload = json.loads(msg.payload.decode())
        uplink = _parse_uplink(payload)
        with _buffer_lock:
            _uplink_buffer.append(uplink)
        logger.debug("MQTT uplink from %s at %s", uplink.device_id, uplink.received_at)
    except Exception:
        logger.exception("Failed to parse MQTT message on topic %s", msg.topic)


def start_mqtt_listener() -> None:
    """Start the MQTT listener in a background daemon thread."""
    if not settings.mqtt_username or not settings.mqtt_password:
        logger.warning("MQTT credentials not configured; real-time listener disabled")
        return

    global _mqtt_client
    _mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    _mqtt_client.username_pw_set(settings.mqtt_username, settings.mqtt_password)

    if settings.mqtt_use_tls:
        _mqtt_client.tls_set(tls_version=ssl.PROTOCOL_TLS_CLIENT)

    _mqtt_client.on_connect = _on_connect
    _mqtt_client.on_message = _on_message

    def _run() -> None:
        try:
            _mqtt_client.connect(settings.mqtt_host, settings.mqtt_port, keepalive=60)
            _mqtt_client.loop_forever()
        except Exception:
            logger.exception("MQTT listener stopped unexpectedly")

    thread = threading.Thread(target=_run, daemon=True, name="mqtt-listener")
    thread.start()
    logger.info("MQTT listener thread started")


def stop_mqtt_listener() -> None:
    """Disconnect the MQTT client."""
    global _mqtt_client
    if _mqtt_client is not None:
        _mqtt_client.disconnect()
        _mqtt_client = None
