import logging
import time

import paho.mqtt.publish as publish
from pyocd.core.helpers import ConnectHelper

MQTT_HOSTNAME = '192.168.0.2'
MQTT_USERNAME = '_USERNAME_'
MQTT_PASSWORD = '_PASSWORD_'
MQTT_CLIENT_ID = 'd9'
SAMPLE_INTERVAL = 30

SENSORS = {'TEMP': [0x20000078, 0.0, 0.1, 1],  # Name, address, value, scale, decimals
           'HUMID': [0x2000007a, 0.0, 0.1, 1],
           'PM25': [0x20000086, 0.0, 1.0, 0],
           'PM10': [0x20000088, 0.0, 1.0, 0],
           'CO2': [0x200000ca, 0.0, 1.0, 0],
           'HCHO': [0x200000f6, 0.0, 0.001, 3],
           'TVOC': [0x20000116, 0.0, 0.001, 3]}
INDEX_ADDR = 0
INDEX_VALUE = 1
INDEX_SCALE = 2
INDEX_DECIMALS = 3

TIMEOUT_SEC = 5

if __name__ == '__main__':
    try:
        time.sleep(TIMEOUT_SEC)
        with ConnectHelper.session_with_chosen_probe(
                options={'target_override': 'gd32f103rc', 'connect_mode': 'attach', 'frequency': 1000000}) as session:
            target = session.target
            target.write32(0x4000042C, 0)  # disable backlight
            while session.is_open:
                start_time = time.time()
                for sensor_elem in SENSORS.keys():
                    SENSORS[sensor_elem][INDEX_VALUE] = round(
                        int(target.read16(SENSORS[sensor_elem][INDEX_ADDR])) * SENSORS[sensor_elem][INDEX_SCALE],
                        SENSORS[sensor_elem][INDEX_DECIMALS])
                    try:
                        publish.single(MQTT_CLIENT_ID + '/sensors/' + sensor_elem,
                                       payload=SENSORS[sensor_elem][INDEX_VALUE],
                                       hostname=MQTT_HOSTNAME,
                                       port=1883, client_id=MQTT_CLIENT_ID,
                                       auth={'username': MQTT_USERNAME, 'password': MQTT_PASSWORD})
                    except Exception:
                        pass  # prevent closing debug session
                time.sleep(SAMPLE_INTERVAL - (time.time() - start_time))
    except Exception:
        logging.exception('Exception')
    finally:
        try:
            target.write32(0x4000042C, 0x64)  # enable backlight
        except Exception:
            pass
        try:
            session.close()
        except Exception:
            pass
