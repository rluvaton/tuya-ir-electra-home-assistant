import time
import logging
from contextlib import contextmanager

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from typing import Any, Callable, Dict, Optional
from .client import AC

from homeassistant.const import (
    ATTR_TEMPERATURE,
    CONF_PASSWORD,
    CONF_USERNAME,
    TEMP_CELSIUS,
)
from homeassistant.components.climate import (
    ClimateEntity,
    PLATFORM_SCHEMA,
)

from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
    HomeAssistantType,
)

from homeassistant.components.climate.const import (
    CURRENT_HVAC_OFF,
    CURRENT_HVAC_IDLE,
    CURRENT_HVAC_COOL,
    CURRENT_HVAC_HEAT,
    CURRENT_HVAC_DRY,
    HVAC_MODE_OFF,
    HVAC_MODE_COOL,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_DRY,
    HVAC_MODE_HEAT,
    HVAC_MODE_HEAT_COOL,
    SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_FAN_MODE,
    FAN_OFF,
    FAN_AUTO,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_HIGH,
)

_LOGGER = logging.getLogger(__name__)

# CONF_AC_ID = "id"
CONF_ACS = "acs"
CONF_AC_NAME = "name"
CONF_AC_TUYA_IR_DEVICE_ID = "tuya_ir_device_id"
CONF_AC_TUYA_DEVICE_LOCAL_KEY = "tuya_device_local_key"
CONF_AC_TUYA_DEVICE_IP = "tuya_device_ip"
CONF_AC_TUYA_DEVICE_VERSION = "tuya_device_version"

DEFAULT_NAME = "TuyaIRElectraHomeAssistant"
print("")


AC_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_AC_NAME, default=DEFAULT_NAME): cv.string,
        vol.Required(CONF_AC_TUYA_IR_DEVICE_ID): cv.string,
        vol.Required(CONF_AC_TUYA_DEVICE_LOCAL_KEY): cv.string,
        vol.Required(CONF_AC_TUYA_DEVICE_IP): cv.string,
        vol.Required(CONF_AC_TUYA_DEVICE_VERSION, default='3.3'): cv.string,
    }
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ACS): vol.All(cv.ensure_list, [AC_SCHEMA]),
    }
)


async def async_setup_platform(
        hass: HomeAssistantType,
        config: ConfigType,
        async_add_entities: Callable,
        discovery_info: Optional[DiscoveryInfoType] = None,
) -> None:
    # Note: since this is a global thing, if at least one entity activates it, it's on
    """Set up the TuyaIRElectraHomeAssistant platform."""
    _LOGGER.debug("Setting up the TuyaIRElectraHomeAssistant climate platform conf: %s", config)
    session = async_get_clientsession(hass)

    acs = [
        TuyaIRElectraHomeAssistant(ac)
        for ac in config.get(CONF_ACS)
    ]

    async_add_entities(acs, update_before_add=True)

    await acs[0].async_setup(hass)


class TuyaIRElectraHomeAssistant(ClimateEntity):
    def __init__(self, ac_conf):
        """Initialize the thermostat."""
        _LOGGER.info("Initializing TuyaIRElectraHomeAssistant", ac_conf)
        self._name = ac_conf[CONF_AC_NAME]
        self.ac = AC(
            ac_conf[CONF_AC_TUYA_IR_DEVICE_ID],
            ac_conf[CONF_AC_TUYA_DEVICE_LOCAL_KEY],
            ac_conf[CONF_AC_TUYA_DEVICE_IP],
            ac_conf[CONF_AC_TUYA_DEVICE_VERSION]
        )

    async def async_setup(self, hass):
        """Set up the thermostat."""
        _LOGGER.info("Setting up TuyaIRElectraHomeAssistant")
        await hass.async_add_executor_job(self.ac.setup)

    # managed properties

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique ID for this thermostat."""
        return "_".join([self._name, "climate"])

    @property
    def should_poll(self):
        """Return if polling is required."""
        # TODO - maybe change that
        return True

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return 16

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return 30

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def current_temperature(self):
        """Return the current temperature."""
        # TODO - I hope that this means in the AC

        if not self.ac.is_on:
            _LOGGER.debug(f"current_temperature: ac is off")
            # return None

        value = self.ac.temp
        if value is not None:
            value = int(value)
        _LOGGER.debug(f"value of current_temperature property: {value}")
        return value

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""

        # TODO - not supported in the moment - will return the current temperature
        if not self.ac.is_on:
            _LOGGER.debug(f"target_temperature: ac is off")
            return None

        value = self.ac.temp
        if value is not None:
            value = int(value)
        _LOGGER.debug(f"value of target_temperature property: {value}")
        return value

    @property
    def target_temperature_step(self):
        return 1

    MODE_BY_NAME = {"IDLE": CURRENT_HVAC_IDLE}

    HVAC_MODE_MAPPING = {
        "STBY": HVAC_MODE_OFF,
        "COOL": HVAC_MODE_COOL,
        "FAN": HVAC_MODE_FAN_ONLY,
        "DRY": HVAC_MODE_DRY,
        "HEAT": HVAC_MODE_HEAT,
        "AUTO": HVAC_MODE_HEAT_COOL,
    }

    HVAC_MODE_MAPPING_INV = {v: k for k, v in HVAC_MODE_MAPPING.items()}

    @property
    def hvac_mode(self):
        """Return hvac operation ie. heat, cool mode."""
        if not self.ac.is_on:
            _LOGGER.debug(f"hvac_mode: ac is off")
            return HVAC_MODE_OFF

        if self.ac.mode == 'cool':
            _LOGGER.debug(f"hvac_mode: ac is cool")
            return HVAC_MODE_COOL

        if self.ac.mode == 'heat':
            _LOGGER.debug(f"hvac_mode: ac is heat")
            return HVAC_MODE_HEAT

        if self.ac.mode == 'auto':
            _LOGGER.debug(f"hvac_mode: ac is auto")
            return HVAC_MODE_HEAT_COOL

        if self.ac.mode == 'fan':
            _LOGGER.debug(f"hvac_mode: ac is fan")
            return HVAC_MODE_FAN_ONLY

        if self.ac.mode == 'dry':
            _LOGGER.debug(f"hvac_mode: ac is dry")
            return HVAC_MODE_DRY

        else:
            _LOGGER.warning(f"hvac_mode: unknown mode: " + self.ac.mode)

            # Not returning off as if it's on then we would be completely off
            return HVAC_MODE_COOL

    @property
    def hvac_modes(self):
        """HVAC modes."""
        return [
            HVAC_MODE_OFF,
            HVAC_MODE_COOL,
            HVAC_MODE_FAN_ONLY,
            HVAC_MODE_DRY,
            HVAC_MODE_HEAT,
            HVAC_MODE_HEAT_COOL,
        ]

    # TODO:!
    # @property
    # def hvac_action(self):
    #     """Return the current running hvac operation."""
    #     # if self._target_temperature < self._current_temperature:
    #     #     return CURRENT_HVAC_IDLE
    #     # return CURRENT_HVAC_HEAT
    #     return CURRENT_HVAC_IDLE

    FAN_MODE_MAPPING = {
        "LOW": FAN_LOW,
        "MED": FAN_MEDIUM,
        "HIGH": FAN_HIGH,
        "AUTO": FAN_AUTO,
    }

    FAN_MODE_MAPPING_INV = {v: k for k, v in FAN_MODE_MAPPING.items()}

    @property
    def fan_mode(self):
        """Returns the current fan mode (low, high, auto etc)"""
        if not self.ac.is_on:
            _LOGGER.debug(f"fan_mode: returning FAN_OFF - device is off")
            return FAN_OFF

        _LOGGER.debug(f"fan_mode: fan_speed is " + self.ac.fan_speed)

        if self.ac.fan_speed == 'low':
            return FAN_LOW

        if self.ac.fan_speed == 'medium':
            return FAN_MEDIUM

        if self.ac.fan_speed == 'high':
            return FAN_HIGH

        if self.ac.fan_speed == 'auto':
            return FAN_AUTO

        _LOGGER.debug(f"fan_mode: unknown fan_speed: " + self.ac.fan_speed)
        return None

    @property
    def fan_modes(self):
        """Fan modes."""
        return [FAN_OFF, FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH]

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_TARGET_TEMPERATURE | SUPPORT_FAN_MODE

    # actions

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        _LOGGER.debug(f"setting new temperature to {temperature}")
        if temperature is None:
            return

        temperature = int(temperature)
        with self._act_and_update():
            self.ac.update_temp(temperature)

        _LOGGER.debug(f"new temperature was set to {temperature}")

    def set_hvac_mode(self, hvac_mode):
        _LOGGER.debug(f"setting hvac mode to {hvac_mode}")
        if hvac_mode == HVAC_MODE_OFF:
            _LOGGER.debug(f"turning off ac due to hvac_mode being set to {hvac_mode}")
            with self._act_and_update():
                self.ac.turn_off()
            _LOGGER.debug(
                f"ac has been turned off due hvac_mode being set to {hvac_mode}"
            )
            return

        ac_mode = None

        if hvac_mode == HVAC_MODE_COOL:
            _LOGGER.debug(f"set_hvac_mode: ac is cool")
            ac_mode = 'cool'

        if hvac_mode == HVAC_MODE_HEAT:
            _LOGGER.debug(f"set_hvac_mode: ac is heat")
            ac_mode = 'heat'

        if hvac_mode == HVAC_MODE_HEAT_COOL:
            _LOGGER.debug(f"set_hvac_mode: ac is auto")
            ac_mode = 'auto'

        if hvac_mode == HVAC_MODE_FAN_ONLY:
            _LOGGER.debug(f"set_hvac_mode: ac is fan")
            ac_mode = 'fan'

        if hvac_mode == HVAC_MODE_DRY:
            _LOGGER.debug(f"set_hvac_mode: ac is dry")
            ac_mode = 'dry'

        if ac_mode is None:
            _LOGGER.warning("Unsupported mode " + hvac_mode)
            return

        _LOGGER.debug(f"setting hvac mode to {hvac_mode} (ac_mode {ac_mode})")
        with self._act_and_update():
            self.ac.update_mode(ac_mode)

        _LOGGER.debug(f"hvac mode was set to {hvac_mode} (ac_mode {ac_mode})")

    def set_fan_mode(self, fan_mode):
        _LOGGER.debug(f"set_fan_mode: setting fan mode to {fan_mode}")
        # if not self.ac.is_on:
        #     _LOGGER.debug(f"set_fan_mode: ac is off, cant set fan mode to {fan_mode}")
        #     return

        fan_speed = None

        if fan_mode == FAN_LOW:
            fan_speed = 'low'

        if fan_mode == FAN_MEDIUM:
            fan_speed = 'medium'

        if fan_mode == FAN_HIGH:
            fan_speed = 'high'

        if fan_mode == FAN_AUTO:
            fan_speed = 'auto'

        if fan_speed is None:
            _LOGGER.warning("Unsupported fan_mode: " + fan_mode)
            return

        _LOGGER.debug(f"setting fan mode to {fan_mode} (fan_speed {fan_speed})")
        with self._act_and_update():
            self.ac.update_fan_speed(fan_speed)
        _LOGGER.debug(f"fan mode was set to {fan_mode} (fan_speed {fan_speed})")

    @contextmanager
    def _act_and_update(self):
        yield
        time.sleep(2)

    # data fetch mechanism
    def update(self):
        """Get the latest data."""
        _LOGGER.debug("not doing anything, should I even use it?")
