#!/usr/bin/env python3

from btlewrap import BluepyBackend, BluetoothBackendException
from mitemp_bt.mitemp_bt_poller import MiTempBtPoller, MI_TEMPERATURE, MI_HUMIDITY, MI_BATTERY
import logging


class GetSensorData:

    def __init__(self):
        self.logger = logging.getLogger('GetSensorData')

    def get(self, mac_address):
        try:
            # Getting data from Mi Temperature and Humidity Sensor
            poller = MiTempBtPoller(mac_address, BluepyBackend)
            return {
                'battery': poller.parameter_value(MI_BATTERY),
                'temperature': poller.parameter_value(MI_TEMPERATURE),
                'humidity': poller.parameter_value(MI_HUMIDITY)
            }
        except BluetoothBackendException:
            self.logger.error('Cannot get sensor data for: ' + mac_address)
            return None
