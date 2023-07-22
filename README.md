# Tuya IR remote for Electra

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=rluvaton&repository=tuya-ir-electra-home-assistant&category=integration)

## HACS Setup
- Add `https://github.com/rluvaton/tuya-ir-electra-home-assistant` as a Custom Repository
- Install `tuya-ir-electra-home-assistant` from the HACS Integrations tab
- Restart Home Assistant
- add to the `configuration.yaml` file the following configuration:

for the `tuya_ir_device_id` and the `tuya_device_local_key` you need to use [`tinytuya`](https://github.com/jasonacox/tinytuya#network-scanner) for those:
  - `python3 -m tinytuya wizard`
```yaml
climate:
  - platform: tuya_ir_electra_home_assistant
    acs:
      - name: AC # Your AC name
        tuya_ir_device_id: "<your Tuya IR device ID>" # it is recommended to use secrets here
        tuya_device_local_key: "<your Tuya device local key>" # it is recommended to use secrets here
        tuya_device_ip: '192.168.1.2' # You tuya device IP
        tuya_device_version: '3.3'
```
- Restart Home Assistant
- Done
