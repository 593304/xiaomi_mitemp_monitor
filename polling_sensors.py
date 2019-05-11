#!/usr/bin/env python3

import configparser
import logging
import psycopg2
import json
import os
import requests

from modules.get_sensor_data import GetSensorData

SENSORS = {
    'bedroom': '4C:65:A8:DB:4A:C2',
    'living_room': '4C:65:A8:DB:49:DF'
}

CONFIG_GROUPS = {
    'database': 'DATABASE',
    'logger': 'LOGGER',
    'server': 'SERVER'
}

CONFIG_KEYS = {
    'db_conn_string': [CONFIG_GROUPS['database'], 'CONNECTION_STRING'],
    'db_temp_file': [CONFIG_GROUPS['database'], 'TEMP_FILE'],
    'logger_file': [CONFIG_GROUPS['logger'], 'FILE'],
    'logger_format': [CONFIG_GROUPS['logger'], 'FORMAT'],
    'server_protocol': [CONFIG_GROUPS['server'], 'PROTOCOL'],
    'server_host': [CONFIG_GROUPS['server'], 'HOST'],
    'server_port': [CONFIG_GROUPS['server'], 'PORT'],
    'server_path': [CONFIG_GROUPS['server'], 'PATH'],
    'server_sensor_values': [CONFIG_GROUPS['server'], 'SENSOR_VALUES']
}

CONFIG = None
CONFIG_FILE = '/mnt/dev/monitoring/Xiaomi_sensor/polling_sensors.conf'

DB_CONNECTION = None
DB_CURSOR = None
FILE = None

LOGGER = None


def init():
    global CONFIG
    CONFIG = configparser.ConfigParser()
    CONFIG.read(CONFIG_FILE)

    db_conn_string = CONFIG_KEYS['db_conn_string']
    db_temp_file = CONFIG_KEYS['db_temp_file']
    logger_file = CONFIG_KEYS['logger_file']
    logger_format = CONFIG_KEYS['logger_format']

    temp_db_file = CONFIG.get(db_temp_file[0], db_temp_file[1])

    global LOGGER
    log_file = CONFIG.get(logger_file[0], logger_file[1])
    logger_format = CONFIG.get(logger_format[0], logger_format[1]).replace('((', '%(')
    logging.basicConfig(filename=log_file, format=logger_format, level=logging.INFO)
    LOGGER = logging.getLogger('polling_sensors')
    try:
        global DB_CONNECTION
        global DB_CURSOR
        DB_CONNECTION = psycopg2.connect(CONFIG.get(db_conn_string[0], db_conn_string[1]))
        DB_CURSOR = DB_CONNECTION.cursor()
        LOGGER.debug('Connected to the database')
        LOGGER.debug('Checking temp file')
        check_temp_file(temp_db_file)
    except Exception:
        LOGGER.error('Cannot connect to the database, using the temporary file')
        global FILE
        FILE = open(temp_db_file, 'a+')


def check_temp_file(temp_db_file):
    try:
        file = open(temp_db_file, 'r')
        lines = file.readlines()
        LOGGER.info('Found temporary file with {} records'.format(len(lines)))
        file.close()
        for line in lines:
            line = json.loads(line)
            save_to_db(line['name'], line['mac_address'], line)
        os.remove(temp_db_file)
    except Exception:
        pass


def save_to_file(name, mac, result):
    LOGGER.debug('Saving to file')
    result['name'] = name
    result['mac_address'] = mac
    FILE.write(json.dumps(result) + '\n')


def save_to_db(name, mac, result):
    LOGGER.debug('Saving to DB ')
    DB_CURSOR.execute(
        'INSERT INTO '
        '  monitoring.sensor_data('
        '    name, mac_address, '
        '    room_temp_celsius, room_humdity_percent, '
        '    battery_percent, '
        '    timestamp) '
        'VALUES('
        '  %s, %s, '
        '  %s, %s, '
        '  %s, '
        '  now())',
        (name, mac,
         result['temperature'], result['humidity'],
         result['battery']))
    DB_CONNECTION.commit()


def main():
    server_protocol = CONFIG_KEYS['server_protocol']
    server_host = CONFIG_KEYS['server_host']
    server_port = CONFIG_KEYS['server_port']
    server_path = CONFIG_KEYS['server_path']
    server_sensor_values = CONFIG_KEYS['server_sensor_values']

    # RPI Dashboard URL
    protocol = CONFIG.get(server_protocol[0], server_protocol[1])
    host = CONFIG.get(server_host[0], server_host[1])
    port = CONFIG.get(server_port[0], server_port[1])
    path = CONFIG.get(server_path[0], server_path[1])
    base_url = "{0}://{1}:{2}/{3}".format(protocol, host, port, path)

    get_sensor_data = GetSensorData()

    for key, value in SENSORS.items():
        LOGGER.debug('Getting values from {0}({1}) sensor'.format(key, value))
        result = get_sensor_data.get(value)
        if result is not None:
            LOGGER.debug('{0} sensor response: {1}'.format(key, json.dumps(result)))
            if DB_CONNECTION is None:
                save_to_file(key, value, result)
            else:
                save_to_db(key, value, result)
        
        # Sending data to the REST APIs
        sensor_values_path = CONFIG.get(server_sensor_values[0], server_sensor_values[1])
        sensor_values_data = {
            'name': key,
            'temperature': result['temperature'],
            'humidity': result['humidity'],
            'battery': result['battery']
        }
        try:
            requests.post("{0}/{1}".format(base_url, sensor_values_path), json=sensor_values_data)
        except Exception as e:
            LOGGER.error(str(e))
        
    if DB_CONNECTION is None:
        FILE.close()
    else:
        DB_CURSOR.close()
        DB_CONNECTION.close()


if __name__ == '__main__':
    init()
    main()
