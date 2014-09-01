import logging
logger = logging.getLogger(__name__)


def _parse_frame(f):
    # Get an array out of the space separated string
    received = f.strip().split()

    # If information message, discard
    if ((received[0] == '>') or (received[0] == '->')):
        return None, ' '.join(received[1:])

    # Check frame not of the form
    # [node val1_lsb val1_msb val2_lsb val2_msb ...]
    # with number of elements odd and at least 3
    if ((not (len(received) & 1)) or (len(received) < 3)):
        raise ValueError(
            "Wrong number of elements: found %d, expected odd number >= 3"
            % len(received))

    # Try to process frame
    try:
        # Only integers are expected
        received = [int(val) for val in received]
    except ValueError:
        raise ValueError("Misformed frame: %s" % received)

    # Get node ID
    node_id = received[0]

    # Recombine transmitted chars into signed int
    values = []
    for i in range(1, len(received), 2):
        value = received[i] + 256 * received[i+1]
        if value > 32768:
            value -= 65536
        values.append(value)

    return node_id, values


class FrameParser:
    def __init__(self, node_definitions):
        self.nodes = {node.id: node for node in node_definitions}

    def process_frame(self, f):
        """Process a frame of data

        f (string): 'NodeID val1_lsb val1_msb val2_lsb val2_msb ...'

        This function recombines the integers and checks their validity.
        Return (node_id, values_dict)

        """
        logger.debug("Frame: %s", f)
        node_id, values = _parse_frame(f)

        if node_id is None:
            logger.info("Message: %s", values)
            return None, {}

        logger.debug("Parsed frame [%d] %s", node_id, values)

        # See if we know about this node
        try:
            node = self.nodes[node_id]
        except KeyError:
            logger.warn("Unknown node id %d" % node_id)
            return None, {}

        values_dict = node.parse_values(values)

        return node, values_dict


