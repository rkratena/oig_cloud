import logging

from homeassistant.components.sensor import SensorEntity
from .oig_cloud import OigCloud
from homeassistant.components.sensor.const import (
    STATE_CLASS_MEASUREMENT,
    STATE_CLASS_TOTAL_INCREASING,
)
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from datetime import timedelta

from .const import CONF_PASSWORD, CONF_USERNAME, SENSOR_TYPES

_LOGGER = logging.getLogger(__name__)


class OigCloudSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, sensor_type):
        self.coordinator = coordinator
        self._sensor_type = sensor_type
        self._attr_state_class = SENSOR_TYPES[sensor_type]["state_class"]
        self._node_id = SENSOR_TYPES[sensor_type]["node_id"]
        self._node_key = SENSOR_TYPES[sensor_type]["node_key"]
        self._box_id = list(self.coordinator.data.keys())[0]
        self.entity_id = f"sensor.oig_{self._box_id}_{sensor_type}"

    @property
    def name(self):
        return SENSOR_TYPES[self._sensor_type]["name"]

    @property
    def device_class(self):
        return SENSOR_TYPES[self._sensor_type]["device_class"]

    @property
    def state(self):
        if self.coordinator.data is None:
            return None

        data = self.coordinator.data
        vals = data.values()
        pv_data = list(vals)[0]

        # computed values
        if self._sensor_type == "ac_in_aci_wtotal":
            return float(
                pv_data["ac_in"]["aci_wr"]
                + pv_data["ac_in"]["aci_ws"]
                + pv_data["ac_in"]["aci_wt"]
            )

        node_value = pv_data[self._node_id][self._node_key]

        if self._sensor_type == "box_prms_mode":
            if node_value == 0:
                return "Home 1"
            elif node_value == 1:
                return "Home 2"
            elif node_value == 2:
                return "Home 3"
            elif node_value == 3:
                return "Home UPS"
            return "Unknown Mode"

        try:
            return float(node_value)
        except ValueError:
            return node_value
        return node_value

    @property
    def unit_of_measurement(self):
        return SENSOR_TYPES[self._sensor_type]["unit_of_measurement"]

    @property
    def unique_id(self):
        return f"oig_cloud_{self._sensor_type}"

    @property
    def should_poll(self):
        # DataUpdateCoordinator handles polling
        return False

    @property
    def state_class(self):
        """Return the state class of the sensor."""
        return SENSOR_TYPES[self._sensor_type]["state_class"]

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


async def async_setup_entry(hass, config_entry, async_add_entities):
    username = config_entry.data[CONF_USERNAME]
    password = config_entry.data[CONF_PASSWORD]
    oig_cloud = OigCloud(username, password)

    async def update_data():
        """Fetch data from API endpoint."""
        return await oig_cloud.get_stats()

    # We create a new DataUpdateCoordinator.
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="sensor",
        update_method=update_data,
        update_interval=timedelta(seconds=60),
    )

    # Fetch initial data so we have data when entities subscribe.
    await coordinator.async_config_entry_first_refresh()

    async_add_entities(
        OigCloudSensor(coordinator, sensor_type) for sensor_type in SENSOR_TYPES
    )