import json
import logging
import time

import paho.mqtt.publish as publish
from pyocd.core.helpers import ConnectHelper

# Name, address, scale, decimals
INDEX_ADDR = 0
INDEX_SCALE = 1
INDEX_DECIMALS = 2
ADDRESS_BACKLIGHT_LEVEL = 0x4000042C
VALUE_BACKLIGHT_EN = 0x64
VALUE_BACKLIGHT_DIS = 0x00

PRIVATE_CONFIG = {}

if __name__ == '__main__':
    try:
        f = open('private_config.json')
        PRIVATE_CONFIG = json.load(f)
        f.close()
        if bool(PRIVATE_CONFIG['MQTT']) and bool(PRIVATE_CONFIG['D9']):
            pass
        with ConnectHelper.session_with_chosen_probe(
                options={'target_override': 'gd32f103rc', 'connect_mode': 'attach', 'frequency': 1000000}) as session:
            session.target.write32(ADDRESS_BACKLIGHT_LEVEL, VALUE_BACKLIGHT_DIS)
            while session.is_open:
                start_time = time.time()
                for sensor in PRIVATE_CONFIG['D9']['SENSORS'].keys():
                    value = round(int(session.target.read16(PRIVATE_CONFIG['D9']['SENSORS'][sensor][INDEX_ADDR])) *
                                  PRIVATE_CONFIG['D9']['SENSORS'][sensor][INDEX_SCALE],
                                  PRIVATE_CONFIG['D9']['SENSORS'][sensor][INDEX_DECIMALS])
                    try:
                        publish.single('d9/sensors/' + sensor,
                                       hostname=PRIVATE_CONFIG['MQTT']['HOSTNAME'], port=1883, client_id='d9',
                                       auth={'username': PRIVATE_CONFIG['MQTT']['USERNAME'],
                                             'password': PRIVATE_CONFIG['MQTT']['PASSWORD']},
                                       payload=value)
                    except Exception:
                        pass
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
