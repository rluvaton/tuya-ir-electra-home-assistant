from threading import Lock

import logging

from .ac_state import ACState
from .ir_api import IRApi

logger = logging.getLogger(__name__ + ".client")

class AC:
    def __init__(self, ir_device_id: str, device_local_key: str, device_ip: str, version: str, state: ACState):
        self._mutex = Lock()

        self._api = IRApi(ir_device_id, device_local_key, device_ip, version)
        self._state = state

        self._status = None
        self._model = None

    def setup(self):
        self._api.setup()

    def update_temp(self, new_temp):
        self.turn_on()
        self.run_with_lock(lambda: self._update_temp_critical(new_temp))

    def _update_temp_critical(self, new_temp):
        res = self._api.set_state(self._state.mode, new_temp, self._state.fan_speed)
        self._update_from_result(res)

    def update_mode(self, mode):
        self.turn_on()
        self.run_with_lock(lambda: self._update_mode_critical(mode))

    def _update_mode_critical(self, new_mode):
        res = self._api.set_state(new_mode, self._state.temp, self._state.fan_speed)
        self._update_from_result(res)

    def update_fan_speed(self, fan_speed):
        self.turn_on()
        self.run_with_lock(lambda: self._update_fan_speed_critical(fan_speed))

    def _update_fan_speed_critical(self, new_fan_speed):
        res = self._api.set_state(self._state.mode, self._state.temp, new_fan_speed)
        self._update_from_result(res)

    def _update_from_result(self, res):
        self._state.mode = res["mode"]
        self._state.fan_speed = res["fan_speed"]
        self._state.temp = int(res["temp"])

    def turn_off(self):
        if self._state.is_on:
            self.toggle_power()

    def turn_on(self):
        if not self._state.is_on:
            self.toggle_power()

    def toggle_power(self):
        self.run_with_lock(self._toggle_power_critical)

    def _toggle_power_critical(self):
        original_is_on = self._state.is_on
        self._api.toggle_power()
        self._state.is_on = not original_is_on
        logger.debug("current on is: " + str(self._state.is_on))

    def run_with_lock(self, critical_section_fn):
        self._mutex.acquire(True)
        try:
            critical_section_fn()
        finally:
            self._mutex.release()
