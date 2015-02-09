#/usr/bin/env python

from paho.mqtt.client import Client
import serial
import time

nodemap = {
    10: 'emontx',
    20: 'emonlcd',
}

client = Client()
client.connect("localhost")
client.loop_start()

s = serial.Serial('/dev/ttyAMA0', 9600)
try:
    while True:
        line = str(s.readline(), encoding='ascii')
        node, values = process_frame(line)
        if node is None:
            continue

        nodename = nodemap[node]
        ts = int(time.time())
        if nodename is 'emontx':
            topic = '/house/electricity/power'
            value = values[0]
        elif nodename is 'emonlcd':
            topic = '/house/livingroom/temperature'
            value = values[0] / 100
        client.publish(topic, value)
        print(ts, topic, value, sep='\t')
finally:
    s.close()
