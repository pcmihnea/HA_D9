import json
import logging
import time

import paho.mqtt.publish as publish
from pyocd.core.helpers import ConnectHelper

# Name: [address, scale, decimals]
INDEX_ADDR = 0
INDEX_SCALE = 1
INDEX_DECIMALS = 2
ADDRESS_BACKLIGHT_LEVEL = 0x4000042C
VALUE_BACKLIGHT_EN = 0x64
VALUE_BACKLIGHT_DIS = 0x00

PRIVATE_CONFIG = {}


def mqtt_publish(topic, payload, retain):
    publish.single(hostname=PRIVATE_CONFIG['MQTT']['HOSTNAME'], port=1883, client_id='d9',
                   auth={'username': PRIVATE_CONFIG['MQTT']['USERNAME'],
                         'password': PRIVATE_CONFIG['MQTT']['PASSWORD']},
                   topic=topic, payload=json.dumps(payload), retain=retain)


if __name__ == '__main__':
    try:
        f = open('private_config.json')
        PRIVATE_CONFIG = json.load(f)
        sensor_values = {}
        f.close()
        if bool(PRIVATE_CONFIG['MQTT']):
            pass
        dev_cfg = {"name": '',
                   "state_topic": 'homeassistant/sensor/D9/state',
                   "value_template": '',
                   "device_class": '',
                   "unit_of_measurement": ''}
        for sensor in PRIVATE_CONFIG['D9']['SENSORS'].keys():
            if 'TEMP' == sensor:
                dev_cfg['device_class'] = 'temperature'
                dev_cfg['unit_of_measurement'] = '°C'
            elif 'HUMID' == sensor:
                dev_cfg['device_class'] = 'humidity'
                dev_cfg['unit_of_measurement'] = '%'
            elif 'PM25' == sensor:
                dev_cfg['device_class'] = 'pm25'
                dev_cfg['unit_of_measurement'] = 'ug/m³'
            elif 'PM10' == sensor:
                dev_cfg['device_class'] = 'pm10'
                dev_cfg['unit_of_measurement'] = 'ug/m³'
            elif 'CO2' == sensor:
                dev_cfg['device_class'] = 'carbon_dioxide'
                dev_cfg['unit_of_measurement'] = 'PPM'
            elif 'HCHO' == sensor:
                dev_cfg['device_class'] = 'volatile_organic_compounds'
                dev_cfg['unit_of_measurement'] = 'mg/m³'
            elif 'TVOC' == sensor:
                dev_cfg['device_class'] = 'volatile_organic_compounds'
                dev_cfg['unit_of_measurement'] = 'mg/m³'
            else:
                continue
            dev_cfg['name'] = 'D9_' + sensor
            dev_cfg['value_template'] = '{{ value_json.' + sensor + ' }}'
            mqtt_publish('homeassistant/sensor/D9_' + sensor + '/config', dev_cfg, True)
        with ConnectHelper.session_with_chosen_probe(
                options={'target_override': 'gd32f103rc', 'connect_mode': 'attach', 'frequency': 1000000}) as session:
            session.target.write32(ADDRESS_BACKLIGHT_LEVEL, VALUE_BACKLIGHT_DIS)
            while session.is_open:
                start_time = time.time()
                for sensor in PRIVATE_CONFIG['D9']['SENSORS'].keys():
                    sensor_values[sensor] = \
                        round(int(session.target.read16(PRIVATE_CONFIG['D9']['SENSORS'][sensor][INDEX_ADDR])) *
                              PRIVATE_CONFIG['D9']['SENSORS'][sensor][INDEX_SCALE],
                              PRIVATE_CONFIG['D9']['SENSORS'][sensor][INDEX_DECIMALS])
                mqtt_publish('homeassistant/sensor/D9/state', sensor_values, False)
                time.sleep(PRIVATE_CONFIG['D9']['SAMPLE_INTERVAL'] - (time.time() - start_time))
    except Exception:
        logging.exception('Exception')
    try:
        session.target.write32(ADDRESS_BACKLIGHT_LEVEL, VALUE_BACKLIGHT_EN)
    except Exception:
        pass
    try:
        session.close()
    except Exception:
        pass
