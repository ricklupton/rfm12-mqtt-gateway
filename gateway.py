import argparse
import asyncio
import serial
from datetime import datetime
import json
import paho.mqtt.client as paho

import logging
logger = logging.getLogger('gateway')

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

        self.mqtt_client = paho.Client()
        self.mqtt_client.on_connect = self._mqtt_on_connect
        self.mqtt_client.on_message = self._mqtt_on_message
        logger.info('Trying to connect to MQTT server...')
        self.mqtt_client.connect("localhost")
        self._mqtt_loop()

    @asyncio.coroutine
    def run_input(self):
        # if isinstance(message, str):
        #     message = message.encode('utf8')
        # writer.write(message)
        # yield from writer.drain()

        # Open serial port
        s = serial.Serial('/dev/ttyAMA0', 9600)
        reader, self.writer = yield from create_read_write_streams(s)

        while True:
            line = yield from reader.readline()
            time = datetime.utcnow().replace(microsecond=0).isoformat()

            logger.debug('Received line: %s', line)
            self.frame_log.writeline(
                '{} {}'.format(time, line.decode('ascii').strip()))

            node, values = self.parser.process_frame(line.decode('ascii'))
            if node is None:
                continue
            logger.debug('Processed frame: %s %s', node, values)

            for k, v in values.items():
                topic = '{}/{}'.format(node.name, k)
                payload = json.dumps({
                    'at':    time,
                    'value': v,
                    'units': node.channels[k].get('units', ''),
                    'description': node.channels[k].get('description', ''),
                })
                logger.debug('Publishing [%s] %s', topic, payload)
                self.mqtt_client.publish(topic, payload)

    def _send_time(self):
         now = datetime.now()
         logger.debug("Broadcasting time %02d:%02d", now.hour, now.minute)
         frame = "00,%02d,%02d,00,s" % (now.hour, now.minute)
         self.writer.write(frame.encode('ascii'))

    def _mqtt_on_connect(self, client, userdata, flags_dict, rc):
        if rc == 0:
            logger.info('Connected to MQTT server')
            # subscribe
            self.mqtt_client.subscribe('/broadcast/#')
        else:
            logger.error('Error connecting to MQTT server (%d): %s',
                         rc, paho.connack_string(rc))

    def _mqtt_on_message(self, client, userdata, message):
        logger.info('Received MQTT message [%s] "%s"',
                    message.topic, message.payload)
        if message.topic == '/broadcast/time':
            self._send_time()

    def _mqtt_loop(self):
        rc = self.mqtt_client.loop(timeout=0)
        if rc != 0:
            logger.error('Error in MQTT loop (%d): %s',
                         rc, paho.error_string(rc))
        self._loop.call_later(1.0, self._mqtt_loop)


def main():
    # Set up logging
    parser = argparse.ArgumentParser(description='emon gateway')
    parser.add_argument('-L', '--log-level', default='warning')
    args = parser.parse_args()

    numeric_level = getattr(logging, args.log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % args.log_level)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s %(name)s [%(levelname)s] %(message)s")
    logging.getLogger('asyncio').setLevel('WARNING')

    gateway = EmonMQTTGateway()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(gateway.run_input())
    loop.close()


if __name__ == '__main__':
    main()
