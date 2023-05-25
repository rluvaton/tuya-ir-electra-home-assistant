import os
import json
from threading import Lock
import tinytuya
import json5

import logging

logger = logging.getLogger(__name__ + ".client")

current_dir = os.path.dirname(__file__)
commands_path = os.path.join(current_dir, './ac-commands.json5')
# Read from json file ac-commands.json
with open(commands_path, 'r') as f:
    ir_commands = json5.load(f)


class IRLearnedApi:
    def __init__(self, tuya_region, tuya_api_key, tuya_api_secret, ir_device_id, ir_remote_id):
       self.tuya_region = tuya_region
       self.tuya_api_key = tuya_api_key
       self.tuya_api_secret = tuya_api_secret
       self._ir_device_id = ir_device_id
       self._ir_remote_id = ir_remote_id

    async def async_setup(self):
        self._tuya_cloud = tinytuya.Cloud(
            apiRegion=self.tuya_region,
            apiKey=self.tuya_api_key,
            apiSecret=self.tuya_api_secret,
            # apiDeviceID=device_id
        )

    def _send_command(self, key_id):
        post_data = {
            # 999 - DIY
            "category_id": 999,
            "key_id": key_id,
        }
        res = self._tuya_cloud.cloudrequest(
            "/v2.0/infrareds/%s/remotes/%s/raw/command" % (self._ir_device_id, self._ir_remote_id),
            post=post_data,
        )

        logger.debug("Send IR command result: %s", json.dumps(res, indent=2))

        if res["success"] is False:
            logger.error("Send IR command failed with %s", json.dumps(res, indent=2))
            raise Exception("Send IR command failed with", json.dumps(res, indent=2))

    def toggle_power(self):
        self._send_command(ir_commands["power_on"])

    def set_state(self, mode, temp, fan_speed):
        if mode not in ['cold', 'hot']:
            logger.error('Mode must be one of cold, hot, got ' + mode)
            raise Exception('Mode must be one of cold, hot, got ' + mode)

        if fan_speed not in ['low', 'medium', 'high', 'auto']:
            logger.error('fan speed must be one of low, medium, high or auto and instead got ' + fan_speed)
            raise Exception('fan speed must be one of low, medium, high or auto and instead got ' + fan_speed)

        bounded_temp = self._format_temp(mode, temp)

        # Got the learning code:
        # https://developer.tuya.com/en/docs/cloud/5c93c9ffc5?id=Kb3oebi2lvz0k
        key_id = ir_commands[mode][fan_speed][str(bounded_temp)]
        self._send_command(key_id)

        return {
            "mode": mode,
            "temp": bounded_temp,
            "fan_speed": fan_speed,
        }

    @staticmethod
    def _format_temp(mode, temp):
        if mode == 'cool':
            # The range of cool temperature is 16-28
            temp = max(temp, 16)
            temp = min(temp, 28)

        if mode == 'hot':
            # The range of cool temperature is 20-30
            temp = min(temp, 20)
            temp = max(temp, 30)

        return temp


def date_diff_in_seconds(dt2, dt1):
    timedelta = dt2 - dt1
    return timedelta.total_seconds()


class AC:
    def __init__(self, tuya_region, tuya_api_key, tuya_api_secret, ir_device_id, ir_remote_id):
        self._mutex = Lock()

        self._api = IRLearnedApi(tuya_region, tuya_api_key, tuya_api_secret, ir_device_id, ir_remote_id)

        # TODO - need to save in persistent storage
        self.is_on = False
        self.mode = 'cold'
        self.fan_speed = 'low'
        self.temp = 25

        self.tmp_temp = None

        self._status = None
        self._model = None

    async def async_setup(self):
        await self._api.async_setup()

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
        if self.is_on:
            self.toggle_power()

    def toggle_power(self):
        self.run_with_lock(self._toggle_power_critical)

    def _toggle_power_critical(self):
        original_is_on = self.is_on
        try:
            self._api.toggle_power()
            self.is_on = not original_is_on
        except Exception as e:
            self.is_on = original_is_on
            raise e

    def run_with_lock(self, critical_section_fn):
        self._mutex.acquire(True)
        try:
            critical_section_fn()
        finally:
            self._mutex.release()
