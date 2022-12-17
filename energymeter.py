#!/usr/bin/env python
#
# Implements IEC 62056-21 / optical "D0" interface
#
# ### Setup
# $ ln -fs /opt/utilitymeters/energymeter.service /etc/systemd/system/energymeter.service
# $ systemctl daemon-reload
# $ systemctl start energymeter.service
# $ systemctl enable energymeter.service

import paho.mqtt.client as mqtt
import re
import serial
import time

tty = serial.Serial(port='/dev/serial/by-id/usb-FTDI_FT230X_Basic_UART_DK0E0X3Z-if00-port0', baudrate=300, parity=serial.PARITY_EVEN, stopbits=serial.STOPBITS_ONE, bytesize=serial.SEVENBITS, timeout=20)

client = mqtt.Client('energymeters')
client.connect('localhost')

while True:
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
        data = re.search(r"1.8.0\*00\(([0-9.]*)", raw_data)
        if data:
            data_value = float(data.group(1))
            client.publish("energy/total_kwh", data_value)
        if raw_data.endswith('!\r\n'):
            etx = tty.read() # end of frame
            bcc = tty.read() # todo check
            break
    time.sleep(0.1)
    tty.baudrate = 300
    time.sleep(1)
    tty.write('\x06'.encode())
    tty.flush()
    time.sleep(30)
