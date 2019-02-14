#!/usr/bin/env python3

import logging
import psycopg2
import json
from subprocess import Popen, PIPE

SENSOR_DATA_COLLECTOR = '/mnt/dev/monitoring/Xiaomi_sensor/get_sensor_data.py'
SENSORS = {
    'bedroom'     : '4c:65:a8:db:4a:c2',
    'living_room' : '4c:65:a8:db:49:df'
}

DB_CONNECTION = None
DB_CURSOR = None
TEMP_DB_FILE = '/mnt/dev/monitoring/Xiaomi_sensor/temp_db'
FILE = None

LOGGER = None
LOGGER_FORMAT = '%(asctime)15s | %(levelname)8s | %(name)s - %(funcName)12s - %(message)s'

def init():
    logging.basicConfig(filename='/mnt/dev/log/python/xiaomi_sensor_polling.log', format=LOGGER_FORMAT, level=logging.DEBUG)
    global LOGGER
    LOGGER = logging.getLogger('polling_sensors')
    try:
        global DB_CONNECTION
        DB_CONNECTION = psycopg2.connect('dbname=adam user=adam')
        global DB_CURSOR
        DB_CURSOR = DB_CONNECTION.cursor()
        LOGGER.debug('Connected to the database')
    except Exception:
        LOGGER.error('Cannot connect to the database, using the temporary file')
        global FILE
        FILE = open(TEMP_DB_FILE, 'a+')

def saveToFile(name, mac, result):
    LOGGER.debug('Saving to file')
    result['name'] = name
    result['mac_address'] = mac
    FILE.write(json.dumps(result) + '\n')

def saveToDB(name, mac, result):
    LOGGER.debug('Saving to DB ')
    DB_CURSOR.execute('INSERT INTO monitoring.sensor_data(name, mac_address, room_temp_celsius, room_humdity_percent, battery_percent, timestamp) VALUES(%s,%s,%s,%s,%s,now())', (name, mac, result['temperature'], result['humidity'], result['battery']))
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
                saveToFile(key, value, stdout)
            else:
                saveToDB(key, value, stdout)
        else:
            LOGGER.error(stderr);
    if DB_CONNECTION is None:
        FILE.close()
    else:
        DB_CURSOR.close()
        DB_CONNECTION.close()

if __name__ == '__main__':
    init()
    main()
