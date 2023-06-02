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
    # Credentials for the IR device
    # From python -m tinytuya scan
    def __init__(self, ir_device_id: str, device_local_key: str, device_ip: str, version: str ='3.3'):
        self.ir_device_id = ir_device_id
        self.device_local_key = device_local_key
        self.device_ip = device_ip
        self.version = float('3.3' if version is None else version)
        self._device_api = None

    def setup(self):
        self._device_api = tinytuya.Device(self.ir_device_id, self.device_ip, self.device_local_key)
        self._device_api.set_version(self.version)

    def _send_command(self, command_id: str):
        payload = self._device_api.generate_payload(tinytuya.CONTROL, {
            "201": json.dumps({
                "control": "send_ir",
                "head": "",
                "key1": command_id,
                "type": 0,
                "delay": 300
            })
        })
        res = self._device_api.send(payload)

        logger.debug("Send IR command result: %s", json.dumps(res, indent=2))

        if res is not None:
            logger.error("Send IR command failed with %s", res)

    def toggle_power(self):
        self._send_command(ir_commands["power_on"])

    def set_state(self, mode, temp, fan_speed):
        if mode not in ['cool', 'heat', 'dry', 'fan', 'auto']:
            msg = 'Mode must be one of cool, heat, dry, fan or auto, got ' + mode
            logger.error(msg)
            raise Exception(msg)

        if fan_speed not in ['low', 'medium', 'high', 'auto']:
            msg = 'fan speed must be one of low, medium, high or auto and instead got ' + fan_speed
            logger.error(msg)
            raise Exception(msg)

        if mode == 'dry':
            # Dry mode only supports low fan speed
            fan_speed = 'low'

        # Got the learning code:
        # https://developer.tuya.com/en/docs/cloud/5c93c9ffc5?id=Kb3oebi2lvz0k
        # Than get the logs through the Tuya dashboard
        key_id = ir_commands[mode][fan_speed][str(temp)]
        self._send_command(key_id)

        return {
            "mode": mode,
            "temp": temp,
            "fan_speed": fan_speed,
        }
