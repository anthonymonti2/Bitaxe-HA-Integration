import logging
from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
    SensorDeviceClass,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import UnitOfTemperature

_LOGGER = logging.getLogger(__name__)

from .const import DOMAIN

SENSOR_NAME_MAP = {
    "frequency": "ASIC Frequency",
    "power": "Power Consumption",
    "temp": "Temperature ASIC",
    "vrTemp": "Temperature VR",
    "hashRate": "Hash Rate",
    "hashRate_1h": "Hash Rate (1hr)",
    "bestDiff": "All-Time Best Difficulty",
    "bestSessionDiff": "Best Session Difficulty",
    "sharesAccepted": "Shares Accepted",
    "sharesRejected": "Shares Rejected",
    "fanspeed": "Fan Speed",
    "fanrpm": "Fan RPM",
    "uptimeSeconds": "Uptime",
}

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up BitAxe sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.unique_id]["coordinator"]
    device_name = entry.data.get("device_name", "BitAxe Miner")

    _LOGGER.debug(f"Setting up sensors for device: {device_name}")

    sensors = [
        BitAxeSensor(coordinator, "frequency", device_name, entry),
        BitAxeSensor(coordinator, "power", device_name, entry),
        BitAxeSensor(coordinator, "temp", device_name, entry),
        BitAxeSensor(coordinator, "vrTemp", device_name, entry),
        BitAxeSensor(coordinator, "hashRate", device_name, entry),
        BitAxeSensor(coordinator, "hashRate_1h", device_name, entry),
        BitAxeSensor(coordinator, "bestDiff", device_name, entry),
        BitAxeSensor(coordinator, "bestSessionDiff", device_name, entry),
        BitAxeSensor(coordinator, "sharesAccepted", device_name, entry),
        BitAxeSensor(coordinator, "sharesRejected", device_name, entry),
        BitAxeSensor(coordinator, "fanspeed", device_name, entry),
        BitAxeSensor(coordinator, "fanrpm", device_name, entry),
        BitAxeSensor(coordinator, "uptimeSeconds", device_name, entry),
    ]

    async_add_entities(sensors, update_before_add=True)


def format_difficulty(value: int) -> str:
    """Convert difficulty values into human-readable units."""
    if value is None:
        return None

    units = [
        (1e18, "E"),
        (1e15, "P"),
        (1e12, "T"),
        (1e9, "G"),
        (1e6, "M"),
        (1e3, "k"),
    ]

    for factor, suffix in units:
        if value >= factor:
            return f"{value / factor:.2f} {suffix}"

    return str(value)


class BitAxeSensor(CoordinatorEntity, SensorEntity):
    """Representation of a BitAxe sensor."""

    def __init__(self, coordinator, sensor_type: str, device_name: str, entry):
        super().__init__(coordinator)

        self.sensor_type = sensor_type
        self.entry = entry
        self._device_name = device_name

        self._attr_name = f"{SENSOR_NAME_MAP.get(sensor_type, sensor_type)} ({device_name})"
        self._attr_unique_id = f"{entry.entry_id}_{sensor_type}"
        self._attr_icon = self._get_icon(sensor_type)

        # Set attributes to allow long term stats
        self._attr_native_unit_of_measurement = self._get_unit(sensor_type)
        self._attr_device_class = self._get_device_class(sensor_type)
        self._attr_state_class = self._get_state_class(sensor_type)

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.entry.entry_id)},
            "name": self._device_name,
            "manufacturer": "Open Source Hardware",
            "model": "BitAxe Miner",
        }

    @property
    def native_value(self):
        value = self.coordinator.data.get(self.sensor_type)

        if value is None:
            return None

        if self.sensor_type == "power":
            return round(float(value), 1)

        if self.sensor_type in {"temp", "vrTemp"}:
            return round(float(value), 1)

        if self.sensor_type in {
            "fanspeed",
            "fanrpm",
            "frequency",
            "hashRate",
            "hashRate_1h",
            "sharesAccepted",
            "sharesRejected",
            "uptimeSeconds",
        }:
            return int(value)

        if self.sensor_type in {"bestDiff", "bestSessionDiff"}:
            return value

        return value

    @property
    def extra_state_attributes(self):
        """Human-readable formatting without breaking statistics."""
        value = self.coordinator.data.get(self.sensor_type)

        if self.sensor_type in {"bestDiff", "bestSessionDiff"} and value is not None:
            return {"formatted": format_difficulty(value)}

        if self.sensor_type == "uptimeSeconds" and value is not None:
            return {"formatted": self._format_uptime(value)}

        return None

    def _get_state_class(self, sensor_type):
        if sensor_type in {
            "frequency",
            "power",
            "temp",
            "vrTemp",
            "hashRate",
            "hashRate_1h",
            "fanspeed",
            "fanrpm",
        }:
            return SensorStateClass.MEASUREMENT

        if sensor_type in {
            "uptimeSeconds",
            "sharesAccepted",
            "sharesRejected",
        }:
            return SensorStateClass.TOTAL_INCREASING

        # bestDiff values should NOT generate statistics
        return None

    def _get_unit(self, sensor_type):
        return {
            "frequency": "MHz",
            "temp": UnitOfTemperature.CELSIUS,
            "vrTemp": UnitOfTemperature.CELSIUS,
            "power": "W",
            "hashRate": "GH/s",
            "hashRate_1h": "GH/s",
            "fanspeed": "%",
            "fanrpm": "RPM",
            "uptimeSeconds": "s",
        }.get(sensor_type)


    def _get_device_class(self, sensor_type):
        return {
            "temp": SensorDeviceClass.TEMPERATURE,
            "vrTemp": SensorDeviceClass.TEMPERATURE,
        }.get(sensor_type)


    @staticmethod
    def _format_uptime(seconds):
        days, remainder = divmod(seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{days}d {hours}h {minutes}m {seconds}s"

    def _get_icon(self, sensor_type):
        if sensor_type == "bestSessionDiff":
            return "mdi:star"
        elif sensor_type == "bestDiff":
            return "mdi:trophy"
        elif sensor_type in ["fanspeed", "fanrpm"]:
            return "mdi:fan"
        elif sensor_type == ["hashRate", "hashRate_1h"]:
            return "mdi:speedometer"
        elif sensor_type == "frequency":
            return "mdi:chip"
        elif sensor_type == "power":
            return "mdi:flash"
        elif sensor_type == "sharesAccepted":
            return "mdi:share"
        elif sensor_type == "sharesRejected":
            return "mdi:share-off"
        elif sensor_type in ["temp", "vrTemp"]:
            return "mdi:thermometer"
        elif sensor_type == "uptimeSeconds":
            return "mdi:clock"
        return "mdi:help-circle"
