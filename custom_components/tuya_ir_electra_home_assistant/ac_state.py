from custom_components.tuya_ir_electra_home_assistant.climate import TuyaIRElectraHomeAssistant

IS_ON_ATTR = 'is_on'
MODE_ATTR = 'mode'
FAN_SPEED_ATTR = 'fan_speed'
TEMP_ATTR = 'temp'


class ACState:
    def __init__(self, entity: TuyaIRElectraHomeAssistant, hass):
        self._hass = hass
        self._entity = entity
        self._is_on = False
        self._mode = 'cool'
        self._fan_speed = 'low'
        self._temp = 25

    def get_entity_id(self, attribute):
        return f'{self._entity.unique_id}.{attribute}'

    @property
    def is_on(self):
        return self._is_on

    @is_on.setter
    def is_on(self, value):
        if value is not True and value is not False:
            raise ValueError('is_on must be True or False')

        self.is_on = value

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, value):
        if value not in ['cool', 'heat', 'dry', 'fan', 'auto']:
            raise ValueError('Mode must be one of cool, heat, dry, fan or auto, got ' + value)

        self._mode = value

    @property
    def fan_speed(self):
        return self._fan_speed

    @fan_speed.setter
    def fan_speed(self, value):
        if value not in ['low', 'medium', 'high', 'auto']:
            raise ValueError('fan speed must be one of low, medium, high or auto and instead got ' + value)

        self._fan_speed = value

    @property
    def temp(self):
        return self._temp

    @temp.setter
    def temp(self, value):
        if value < 16 or value > 30:
            raise ValueError('temp must be between 16 and 30, got ' + str(value))

        self._temp = value

    def set_initial_state(self, is_on, mode, temp, fan_speed):
        if is_on is None:
            is_on = False
        self.is_on = is_on

        if mode is None:
            mode = 'cool'
        self.mode = mode

        if temp is None:
            temp = 25
        self.temp = temp

        if fan_speed is None:
            fan_speed = 'low'
        self.fan_speed = fan_speed
