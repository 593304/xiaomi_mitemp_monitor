#!/usr/bin/env python3

import logging
import psycopg2
import json
import os
from subprocess import Popen, PIPE

SENSOR_DATA_COLLECTOR = '/mnt/dev/monitoring/Xiaomi_sensor/get_sensor_data.py'
SENSORS = {
    'bedroom': '4C:65:A8:DB:4A:C2',
    'living_room': '4C:65:A8:DB:49:DF'
}

DB_CONNECTION = None
DB_CURSOR = None
TEMP_DB_FILE = '/mnt/dev/monitoring/Xiaomi_sensor/temp_db'
FILE = None

LOGGER = None
LOG_FILE = '/mnt/dev/log/python/xiaomi_sensor_polling.log'
LOGGER_FORMAT = '%(asctime)15s | %(levelname)8s | %(name)s - %(funcName)12s - %(message)s'


def init():
    logging.basicConfig(filename=LOG_FILE, format=LOGGER_FORMAT, level=logging.INFO)
    global LOGGER
    LOGGER = logging.getLogger('polling_sensors')
    try:
        global DB_CONNECTION
        DB_CONNECTION = psycopg2.connect('dbname=adam user=adam')
        global DB_CURSOR
        DB_CURSOR = DB_CONNECTION.cursor()
        LOGGER.debug('Connected to the database')
        LOGGER.debug('Checking temp file')
        check_temp_file()
    except Exception:
        LOGGER.error('Cannot connect to the database, using the temporary file')
        global FILE
        FILE = open(TEMP_DB_FILE, 'a+')


def check_temp_file():
    try:
        file = open(TEMP_DB_FILE, 'r')
        lines = file.readlines()
        LOGGER.info('Found temporary file with {} records'.format(len(lines)))
        file.close()
        for line in lines:
            line = json.loads(line)
            save_to_db(line['name'], line['mac_address'], line)
        os.remove(TEMP_DB_FILE)
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
    for key, value in SENSORS.items():
        LOGGER.debug('Getting values from {0}({1}) sensor'.format(key, value))
        process = Popen([SENSOR_DATA_COLLECTOR, value], stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        if not stderr:
            stdout = json.loads('{' + stdout.decode('utf-8').rstrip() + '}')
            LOGGER.debug('{0} sensor response: {1}'.format(key, stdout))
            if DB_CONNECTION is None:
                save_to_file(key, value, stdout)
            else:
                save_to_db(key, value, stdout)
        else:
            LOGGER.error('Cannot connect to sensor: {0}({1})'.format(key, value), stderr)
    if DB_CONNECTION is None:
        FILE.close()
    else:
        DB_CURSOR.close()
        DB_CONNECTION.close()


if __name__ == '__main__':
    init()
    main()
