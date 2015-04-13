import asyncio
import serial
from datetime import datetime
import json
import paho.mqtt.client as paho
import logging

from .parser import FrameParser
from .nodes import load_definitions_from_yaml
from .textfilewriter import TextFileWriter

logger = logging.getLogger('gateway')


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

        self.frame_log = TextFileWriter('/mnt/stick/frame_log', 'frames')

        with open('nodes.yaml', 'rt') as f:
            nodes = load_definitions_from_yaml(f.read())
        self.nodes_by_name = {node.name: node for node in nodes}
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

    def _send_command(self, node_name, command_name, values):
        try:
            node = self.nodes_by_name[node_name]
        except KeyError:
            logger.error("Unknown node name '%s'", node_name)
            return

        try:
            values = json.loads(values.decode('utf8'))
        except Exception as err:
            logger.error("Error parsing JSON: %r", err)
            return

        logger.info("Sending command '%s' to node '%s'",
                    command_name, node_name)
        try:
            payload = node.encode_command(command_name, values)
        except Exception as err:
            logger.error("Error encoding command: %r", err)
        else:
            self._write_payload(node.id, payload)

    def _write_payload(self, node_id, payload):
        frame = ','.join(['%02d' % x for x in payload]) + ',%ds' % node_id
        logger.debug('Writing line: %s', frame)
        self.writer.write(frame.encode('ascii'))

    def _mqtt_on_connect(self, client, userdata, flags_dict, rc):
        if rc == 0:
            logger.info('Connected to MQTT server')
            # subscribe
            self.mqtt_client.subscribe('/send_command/#')
        else:
            logger.error('Error connecting to MQTT server (%d): %s',
                         rc, paho.connack_string(rc))

    def _mqtt_on_message(self, client, userdata, message):
        logger.info('Received MQTT message [%s] "%s"',
                    message.topic, message.payload)
        if not message.topic.startswith('/'):
            return
        parts = message.topic[1:].split('/')
        if parts[0] == 'send_command':
            if len(parts) < 3:
                logger.error('Bad send_command topic: "%s"', message.topic)
            else:
                self._send_command('/'.join([''] + parts[1:-1]), parts[-1],
                                   message.payload)

    def _mqtt_loop(self):
        rc = self.mqtt_client.loop(timeout=0)
        if rc != 0:
            logger.error('Error in MQTT loop (%d): %s',
                         rc, paho.error_string(rc))
        self._loop.call_later(1.0, self._mqtt_loop)
