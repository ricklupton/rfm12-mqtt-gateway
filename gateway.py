import asyncio
import serial
from datetime import datetime
import json
from paho.mqtt.client import Client, error_string

import logging

import sys
sys.path.append('..')
from emon.parser import FrameParser
from emon.nodes import load_definitions_from_yaml
from emon.textfilewriter import TextFileWriter


@asyncio.coroutine
def create_read_write_streams(handle, loop=None):
    if loop is None:
        loop = asyncio.get_event_loop()

    # Set up StreamWriter
    writer_transport, writer_protocol = yield from loop.connect_write_pipe(
        asyncio.streams.FlowControlMixin, handle)
    writer = asyncio.StreamWriter(writer_transport, writer_protocol, None, loop)

    # Set up StreamReader
    reader = asyncio.StreamReader()
    reader_protocol = asyncio.StreamReaderProtocol(reader)
    yield from loop.connect_read_pipe(lambda: reader_protocol, handle)

    return reader, writer


class EmonMQTTGateway:
    def __init__(self, loop=None):
        if loop is None:
            loop = asyncio.get_event_loop()
        self._loop = loop

        self.frame_log = TextFileWriter('frame_log', 'frames')

        with open('nodes.yaml', 'rt') as f:
            nodes = load_definitions_from_yaml(f.read())
        self.parser = FrameParser(nodes)

        self.mqtt_client = Client()
        def on_connect(client, userdata, rc):
            print('------- connected to mqtt')
        self.mqtt_client.on_connect = on_connect
        def on_log(client, userdata, level, buf):
            print('******', level, buf)
        self.mqtt_client.on_log = on_log
        print('connecting................')
        print(self.mqtt_client.connect("localhost"))
        self._mqtt_loop()

    @asyncio.coroutine
    def run_input(self):
        # if isinstance(message, str):
        #     message = message.encode('utf8')
        # writer.write(message)
        # yield from writer.drain()

        # Open serial port
        s = serial.Serial('/dev/ttyAMA0', 9600)
        reader, writer = yield from create_read_write_streams(s)

        while True:
            line = yield from reader.readline()
            time = datetime.utcnow().replace(microsecond=0).isoformat()
            self.frame_log.writeline(
                '{} {}'.format(time, line.decode('ascii').strip()))
            # print("Line:", repr(line.decode('utf8')))
            # line = str(self.input_stream.readline(), encoding='ascii')
            node, values = self.parser.process_frame(line)
            if node is None:
                continue
            for k, v in values.items():
                topic = '{}/{}'.format(node.name, k)
                payload = json.dumps({
                    'at':    time,
                    'value': v,
                    'units': node.channels[k].get('units', ''),
                    'description': node.channels[k].get('description', ''),
                })
                print('publish', topic, payload)
                self.mqtt_client.publish(topic, payload)

    def _mqtt_loop(self):
        print('periodically running...')
        print(self.mqtt_client.loop(timeout=0))
        self._loop.call_later(1.0, self._mqtt_loop)


gateway = EmonMQTTGateway()
loop = asyncio.get_event_loop()
loop.run_until_complete(gateway.run_input())
loop.close()
