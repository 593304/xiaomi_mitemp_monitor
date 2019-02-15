#!/usr/bin/env python3

import argparse

from btlewrap import BluepyBackend
from mitemp_bt.mitemp_bt_poller import MiTempBtPoller, MI_TEMPERATURE, MI_HUMIDITY, MI_BATTERY


def main():
    # Getting mac address
    parser = argparse.ArgumentParser()
    parser.add_argument('mac')
    args = parser.parse_args()
    
    # Getting data from Mi Temperature and Humidity Sensor
    poller = MiTempBtPoller(args.mac, BluepyBackend)
    result = '"battery": {0}, "temperature": {1}, "humidity": {2}'.format(poller.parameter_value(MI_BATTERY), poller.parameter_value(MI_TEMPERATURE), poller.parameter_value(MI_HUMIDITY))
    
    print(result)

if __name__ == '__main__':
    main()
