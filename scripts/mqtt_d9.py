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


def mqtt_discovery(sn):
    dev_cfg = {"name": '',
               "state_topic": 'homeassistant/sensor/D9/state',
               "value_template": '',
               "device_class": '',
               "unit_of_measurement": '',
               "expire_after": 600}
    unique_id = 0
    for device in PRIVATE_CONFIG['D9']['SENSORS'].keys():
        if 'TEMP' == device:
            dev_cfg['device_class'] = 'temperature'
            dev_cfg['unit_of_measurement'] = '°C'
        elif 'HUMID' == device:
            dev_cfg['device_class'] = 'humidity'
            dev_cfg['unit_of_measurement'] = '%'
        elif 'PM25' == device:
            dev_cfg['device_class'] = 'pm25'
            dev_cfg['unit_of_measurement'] = 'ug/m³'
        elif 'PM10' == device:
            dev_cfg['device_class'] = 'pm10'
            dev_cfg['unit_of_measurement'] = 'ug/m³'
        elif 'CO2' == device:
            dev_cfg['device_class'] = 'carbon_dioxide'
            dev_cfg['unit_of_measurement'] = 'PPM'
        elif 'HCHO' == device:
            dev_cfg['device_class'] = 'volatile_organic_compounds'
            dev_cfg['unit_of_measurement'] = 'mg/m³'
        elif 'TVOC' == device:
            dev_cfg['device_class'] = 'volatile_organic_compounds'
            dev_cfg['unit_of_measurement'] = 'mg/m³'
        else:
            continue
        dev_cfg['name'] = 'D9_' + device
        dev_cfg['value_template'] = '{{ value_json.' + device + ' }}'
        dev_cfg['unique_id'] = sn + str(unique_id)
        unique_id += 1
        mqtt_publish('homeassistant/sensor/D9_' + device + '/config', dev_cfg, True)


if __name__ == '__main__':
    try:
        logging.info('INIT')
        f = open('private_config.json')
        PRIVATE_CONFIG = json.load(f)
        sensor_values = {}
        f.close()
        if bool(PRIVATE_CONFIG['MQTT']):
            pass
        logging.info('LOOP')
        with ConnectHelper.session_with_chosen_probe(
                options={'target_override': 'gd32f103rc', 'connect_mode': 'attach', 'frequency': 1000000}) as session:
            mqtt_discovery(sn=session.probe.unique_id)
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
        logging.exception('EXCEPTION')
    try:
        session.target.write32(ADDRESS_BACKLIGHT_LEVEL, VALUE_BACKLIGHT_EN)
    except Exception:
        pass
    try:
        session.close()
    except Exception:
        pass
