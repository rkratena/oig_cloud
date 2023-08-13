import logging

from .binary_sensor_types import BINARY_SENSOR_TYPES
from .const import DEFAULT_NAME, DOMAIN


from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
)
from .binary_sensor_types import BINARY_SENSOR_TYPES
from .api.oig_cloud_api import OigCloudApi

_LOGGER = logging.getLogger(__name__)


class OigCloudBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a binary sensor entity for OIG Cloud.

    This class handles the state and attributes of a binary sensor entity for OIG Cloud.
    It uses a CoordinatorEntity to manage the data updates and a BinarySensorEntity to
    represent the entity in Home Assistant.

    Args:
        coordinator (DataUpdateCoordinator): The coordinator that manages the data updates.
        sensor_type (str): The type of the binary sensor.

    Attributes:
        entity_id (str): The entity ID of the binary sensor.
        name (str): The name of the binary sensor.
        device_class (str): The device class of the binary sensor.
        state (bool): The state of the binary sensor.
        unique_id (str): The unique ID of the binary sensor.
        should_poll (bool): Whether the binary sensor should be polled.
        entity_category (str): The entity category of the binary sensor.
        device_info (dict): The device information of the binary sensor.

    """

    def __init__(self, coordinator, sensor_type):
        self.coordinator = coordinator
        self._sensor_type = sensor_type
        self._node_id = BINARY_SENSOR_TYPES[sensor_type]["node_id"]
        self._node_key = BINARY_SENSOR_TYPES[sensor_type]["node_key"]
        self._box_id = list(self.coordinator.data.keys())[0]
        self.entity_id = f"binary_sensor.oig_{self._box_id}_{sensor_type}"
        _LOGGER.debug(f"Created binary sensor {self.entity_id}")

    @property
    def name(self):
        """Return the name of the sensor."""
        language = self.hass.config.language
        if language == "cs":
            return BINARY_SENSOR_TYPES[self._sensor_type]["name_cs"]
        return BINARY_SENSOR_TYPES[self._sensor_type]["name"]

    @property
    def device_class(self):
        return BINARY_SENSOR_TYPES[self._sensor_type]["device_class"]

    @property
    def state(self):
        _LOGGER.debug(f"Getting state for {self.entity_id}")
        if self.coordinator.data is None:
            _LOGGER.debug(f"Data is None for {self.entity_id}")
            return None

        data = self.coordinator.data
        vals = data.values()
        pv_data = list(vals)[0]

        node_value = pv_data[self._node_id][self._node_key]

        val = bool(node_value)

        return val

    @property
    def unique_id(self):
        return f"oig_cloud_{self._sensor_type}"

    @property
    def should_poll(self):
        # DataUpdateCoordinator handles polling
        return False

    @property
    def entity_category(self):
        return BINARY_SENSOR_TYPES[self._sensor_type].get("entity_category")

    @property
    def device_info(self):
        data = self.coordinator.data
        vals = data.values()
        pv_data = list(vals)[0]
        is_queen = pv_data["queen"]
        if is_queen:
            model_name = f"{DEFAULT_NAME} Queen"
        else:
            model_name = f"{DEFAULT_NAME} Home"

        return {
            "identifiers": {(DOMAIN, self._box_id)},
            "name": f"{model_name} {self._box_id}",
            "manufacturer": "OIG",
            "model": model_name,
        }

    async def async_added_to_hass(self):
        self.async_on_remove(
            self.coordinator.async_add_listener(self._handle_coordinator_update)
        )
        self._handle_coordinator_update()

    def _handle_coordinator_update(self):
        self.async_write_ha_state()

    async def async_update(self):
        # Request the coordinator to fetch new data and update the entity's state
        await self.coordinator.async_request_refresh()