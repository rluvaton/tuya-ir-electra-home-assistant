import os
import json
import tinytuya
import json5

import logging

logger = logging.getLogger(__name__ + ".client.ir_api")

current_dir = os.path.dirname(__file__)
commands_path = os.path.join(current_dir, './ac-commands.json5')
# Read from json file ac-commands.json
with open(commands_path, 'r') as f:
    ir_commands = json5.load(f)

class IRApi:
    def __init__(self, tuya_region, tuya_api_key, tuya_api_secret, ir_device_id, ir_remote_id):
       self.tuya_region = tuya_region
       self.tuya_api_key = tuya_api_key
       self.tuya_api_secret = tuya_api_secret
       self._ir_device_id = ir_device_id
       self._ir_remote_id = ir_remote_id

    def setup(self):
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
        if mode == 'cold':
            # The range of cool temperature is 16-28
            temp = max(temp, 16)
            temp = min(temp, 28)

        if mode == 'hot':
            # The range of cool temperature is 20-30
            temp = min(temp, 20)
            temp = max(temp, 30)

        return temp
