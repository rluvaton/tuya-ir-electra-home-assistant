from threading import Lock

import logging
from .ir_api import IRApi

logger = logging.getLogger(__name__ + ".client")

class AC:
    def __init__(self, tuya_region, tuya_api_key, tuya_api_secret, ir_device_id, ir_remote_id):
        self._mutex = Lock()

        self._api = IRApi(tuya_region, tuya_api_key, tuya_api_secret, ir_device_id, ir_remote_id)

        # TODO - need to save in persistent storage
        self.is_on = False
        self.mode = 'cold'
        self.fan_speed = 'low'
        self.temp = 25

        self.tmp_temp = None

        self._status = None
        self._model = None

    def setup(self):
        self._api.setup()

    def update_temp(self, new_temp):
        self.turn_on()
        self.run_with_lock(lambda: self._update_temp_critical(new_temp))

    def _update_temp_critical(self, new_temp):
        res = self._api.set_state(self.mode, new_temp, self.fan_speed)
        self.temp = res["temp"]

    def update_mode(self, mode):
        self.turn_on()
        self.run_with_lock(lambda: self._update_mode_critical(mode))

    def _update_mode_critical(self, new_mode):
        res = self._api.set_state(new_mode, self.temp, self.fan_speed)
        self.mode = res["mode"]

    def update_fan_speed(self, fan_speed):
        self.turn_on()
        self.run_with_lock(lambda: self._update_fan_speed_critical(fan_speed))

    def _update_fan_speed_critical(self, new_fan_speed):
        res = self._api.set_state(self.mode, self.temp, new_fan_speed)
        self.fan_speed = res["fan_speed"]

    def turn_off(self):
        if self.is_on:
            self.toggle_power()

    def turn_on(self):
        if not self.is_on:
            self.toggle_power()

    def toggle_power(self):
        self.run_with_lock(self._toggle_power_critical)

    def _toggle_power_critical(self):
        original_is_on = self.is_on
        try:
            self._api.toggle_power()
            self.is_on = not original_is_on
            logger.debug("current on is: " + str(self.is_on))
        except Exception as e:
            self.is_on = original_is_on
            raise e

    def run_with_lock(self, critical_section_fn):
        self._mutex.acquire(True)
        try:
            critical_section_fn()
        finally:
            self._mutex.release()
