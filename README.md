# LoRaWAN Schnittstelle

Eine REST-API-Schnittstelle, die LoRaWAN-Gerätedaten von **The Things Network (TTN) v3** abfragt, als JSON formatiert und über eine HTTP-API bereitstellt.

## Features

- 📡 **Geräteliste** – alle Endgeräte einer TTN-Anwendung abfragen
- 📥 **Gespeicherte Uplinks** – historische Uplink-Nachrichten aus dem TTN Storage Integration abrufen
- ⚡ **Live-Uplinks** – Echtzeit-Nachrichten über MQTT empfangen und im Puffer bereitstellen
- 📄 **JSON-API** – alle Daten sauber als JSON formatiert
- 📚 **Automatische API-Dokumentation** – Swagger UI unter `/docs`, ReDoc unter `/redoc`

## Voraussetzungen

- Python 3.12+
- The Things Network v3 Account mit einer Anwendung und API-Key
- (Optional) TTN Storage Integration für historische Uplinks aktiviert

## Installation

```bash
pip install -r requirements.txt
```

## Konfiguration

Kopiere `.env.example` nach `.env` und trage deine TTN-Zugangsdaten ein:

```bash
cp .env.example .env
```

| Variable | Beschreibung | Beispiel |
|---|---|---|
| `TTN_API_KEY` | TTN API-Schlüssel | `NNSXS.AAAA...` |
| `TTN_APP_ID` | Application ID | `my-sensor-app` |
| `TTN_TENANT_ID` | TTN Tenant | `ttn` |
| `TTN_BASE_URL` | API-Basis-URL | `https://eu1.cloud.thethings.network` |
| `MQTT_HOST` | MQTT-Broker | `eu1.cloud.thethings.network` |
| `MQTT_PORT` | MQTT-Port (TLS) | `8883` |
| `MQTT_USERNAME` | MQTT Benutzername | `my-app@ttn` |
| `MQTT_PASSWORD` | MQTT Passwort (= API-Key) | `NNSXS.AAAA...` |
| `API_HOST` | API-Bind-Adresse | `0.0.0.0` |
| `API_PORT` | API-Port | `8000` |

## Starten

```bash
python run.py
```

Die API ist dann unter `http://localhost:8000` erreichbar.

## API-Endpunkte

| Methode | Pfad | Beschreibung |
|---|---|---|
| `GET` | `/api/v1/devices` | Alle Geräte einer Anwendung |
| `GET` | `/api/v1/devices/{device_id}` | Ein einzelnes Gerät |
| `GET` | `/api/v1/devices/{device_id}/uplinks` | Gespeicherte Uplinks eines Geräts |
| `GET` | `/api/v1/uplinks/live` | Live-Uplinks aus dem MQTT-Puffer |

### Beispiel

```bash
# Alle Geräte auflisten
curl http://localhost:8000/api/v1/devices

# Uplinks eines Geräts abrufen (max. 10)
curl "http://localhost:8000/api/v1/devices/sensor-01/uplinks?limit=10"

# Live-Uplinks aus dem MQTT-Puffer
curl http://localhost:8000/api/v1/uplinks/live
```

### Beispiel-Antwort (Uplink)

```json
{
  "messages": [
    {
      "device_id": "sensor-01",
      "application_id": "my-sensor-app",
      "received_at": "2024-01-15T12:00:00Z",
      "f_cnt": 42,
      "f_port": 1,
      "payload_raw": "AQID",
      "payload_decoded": {"temperature": 22.5, "humidity": 60},
      "rssi": -85,
      "snr": 7.5,
      "spreading_factor": 7,
      "bandwidth": 125000,
      "gateway_id": "my-gateway"
    }
  ],
  "total": 1
}
```

## Tests

```bash
python -m pytest tests/ -v
```

## Projektstruktur

```
.
├── app/
│   ├── main.py           # FastAPI-App (Einstiegspunkt)
│   ├── config.py         # Konfiguration (Umgebungsvariablen)
│   ├── models.py         # Datenmodelle (Pydantic)
│   ├── api/
│   │   └── routes.py     # API-Routen
│   └── lorawan/
│       ├── client.py     # TTN HTTP-API-Client
│       └── mqtt_listener.py  # MQTT-Echtzeit-Listener
├── tests/
│   ├── test_api.py       # API-Tests
│   └── test_lorawan_client.py  # Parsing-Tests
├── run.py                # Startskript
├── requirements.txt
└── .env.example
```

