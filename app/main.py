"""LoRaWAN API – FastAPI application entry point."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.lorawan.mqtt_listener import start_mqtt_listener, stop_mqtt_listener

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s – %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    logger.info("Starting LoRaWAN Schnittstelle …")
    start_mqtt_listener()
    yield
    logger.info("Shutting down …")
    stop_mqtt_listener()


app = FastAPI(
    title="LoRaWAN Schnittstelle",
    description=(
        "REST API for querying LoRaWAN device data from The Things Network (TTN) v3. "
        "Exposes device lists, stored uplink messages as JSON, and a real-time MQTT buffer."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/", include_in_schema=False)
async def root():
    return {"message": "LoRaWAN Schnittstelle läuft. Dokumentation: /docs"}
