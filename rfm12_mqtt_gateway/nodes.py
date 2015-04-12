import struct
import yaml
import logging
logger = logging.getLogger(__name__)


class NodeDefinition:
    def __init__(self, name, node_id, payload_format,
                 channels=None, commands=None):
        self.name = name
        self.id = node_id
        self.payload_format = payload_format
        self.channels = channels if channels is not None else {}
        self.commands = commands if commands is not None else {}

    def parse_values(self, values):
        result = {}
        for k, channel in self.channels.items():
            try:
                logger.debug("eval '%s' with %s", channel['value'], values)
                value = eval(channel['value'], dict(x=values))
            except IndexError:
                raise ValueError("Not enough values")
            except NameError:
                raise RuntimeError("Expression used name other than 'x'")
            else:
                result[k] = value
        return result

    def parse_payload(self, payload):
        # Unpack the data
        fmt = '<' + self.payload_format
        expected_len = struct.calcsize(fmt)
        if len(payload) != expected_len:
            raise ValueError(
                "Bad payload length (expected {} bytes for format '{}', got {}"
                .format(expected_len, fmt, len(payload)))
        data = struct.unpack(fmt, payload)
        logger.debug("Node %d: parsed payload %s", self.id, data)

        # Process into final values dictionary
        return self.parse_values(data)

    def encode_command(self, command_name, values):
        command = self.commands[command_name]
        try:
            logger.debug("eval '%s' with %s", command['values'], values)
            values = eval(command['values'], dict(x=values))
        except IndexError:
            raise ValueError("Not enough values")
        except NameError:
            raise RuntimeError("Expression used name other than 'x'")

        # Pack data
        fmt = '<' + command['payload']
        try:
            payload = struct.pack(fmt, *values)
        except struct.error:
            raise ValueError(("Wrong number of values ({}) for payload format "
                              "'{}' while processing command '{}'")
                             .format(len(values), fmt, command_name))
        return payload

    def __repr__(self):
        return "<NodeDefinition #{} {}>".format(self.id, self.name)

    def __eq__(self, other):
        return type(self) == type(other) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self.__eq__(other)


def _ensure_values_are_strings(channels):
    for k, v in channels.items():
        if 'value' in v:
            v['value'] = str(v['value'])
        if 'values' in v:
            v['values'] = str(v['values'])
    return channels


def load_definitions_from_yaml(stream):
    data = yaml.safe_load(stream)
    return [
        NodeDefinition(d['name'], d['node_id'], d['payload'],
                       _ensure_values_are_strings(d.get('channels', {})),
                       _ensure_values_are_strings(d.get('commands', {})))
        for d in data
    ]
