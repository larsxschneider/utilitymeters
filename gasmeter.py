#!/usr/bin/env python
#
# Implements IEC 62056-21 / optical "D0" interface
#
# ### Setup
# $ ln -fs /opt/utilitymeters/gasmeter.service /etc/systemd/system/gasmeter.service
# $ systemctl daemon-reload
# $ systemctl start gasmeter.service
# $ systemctl enable gasmeter.service

import paho.mqtt.client as mqtt
import re
import serial
import time

delta=2580.923
tty = serial.Serial(
        port='/dev/serial/by-id/usb-FTDI_WEIDMANN_GAS_A17PEL80-if00-port0', 
        baudrate=300, 
        parity=serial.PARITY_EVEN, 
        stopbits=serial.STOPBITS_ONE, 
        bytesize=serial.SEVENBITS, 
        timeout=20)
client = mqtt.Client('gasmeters')
client.connect('localhost')

while True:
    print("Sign-on", flush=True)
    tty.write('/?!\r\n'.encode())
    tty.flush()
    tty.read_until()
    time.sleep(1)
    tty.write('\x06050\r\n'.encode())
    tty.flush()
    time.sleep(0.1)
    tty.baudrate = 9600
    stx = tty.read() # start of frame
    while True:
        raw_data = tty.read_until().decode("utf-8")
        print(raw_data, flush=True)
        data = re.search(r"7-0:(\d\.\d\.\d)\(([0-9.]*)", raw_data)
        if data:
            data_type = data.group(1)
            data_value = float(data.group(2))
            if data_type == '3.0.0':
                client.publish("gas/total_m3", delta + data_value)
            elif data_type == '1.7.0':
                client.publish("gas/current_m3/h", data_value)
        elif raw_data == '!\r\n':
            etx = tty.read() # end of frame
            bcc = tty.read() # todo check
            break
    print("Sign-off", flush=True)
    time.sleep(0.1)
    tty.baudrate = 300
    time.sleep(1)
    tty.write('\x06'.encode())
    tty.flush()
    time.sleep(30)
