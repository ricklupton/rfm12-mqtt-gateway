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
        if f.strip().startswith(('>', '->')):
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
            logger.warning("Unknown node id %d" % node_id)
            return None, {}

        return node, node.parse_payload(buffer[1:])
