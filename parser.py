import struct
import logging
logger = logging.getLogger(__name__)


class FrameParser:
    def __init__(self, node_definitions):
        self.nodes = {node.id: node for node in node_definitions}

    def process_frame(self, f):
        """Process a frame of data.

        f is a space-separated string containing a sequence of
        integers representing the bytes of the message. The first byte
        is the node ID. This function recombines the integers
        according to the sending node's payload format and checks
        their validity.

        Returns (node, values_dict)
        """
        logger.debug("Frame: %s", f)

        # Just return command echos and responses
        if f.startswith(('>', '->')):
            return None, f.strip().lstrip('>- ')

        # Try to process frame - expect space-separated integers
        try:
            buffer = bytes([int(val) for val in f.strip().split()])
        except ValueError:
            raise ValueError("Misformed frame: %s" % f.strip())

        # Look up node id
        node_id = buffer[0]
        try:
            node = self.nodes[node_id]
        except KeyError:
            logger.warn("Unknown node id %d" % node_id)
            return None, {}

        # Unpack the data
        fmt = '<b' + node.payload_format
        expected_len = struct.calcsize(fmt)
        if len(buffer) != expected_len:
            raise ValueError(
                "Bad frame length (expected {} bytes for format '{}', got {}"
                .format(expected_len, fmt, len(buffer)))
        data = struct.unpack(fmt, buffer)
        logger.debug("Node %d: parsed frame %s", node_id, data)

        # Process into final values dictionary
        values_dict = node.parse_values(data[1:])

        return node, values_dict
