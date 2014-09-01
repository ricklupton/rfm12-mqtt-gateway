import yaml
import logging
logger = logging.getLogger(__name__)


class NodeDefinition:
    def __init__(self, node_id, channels):
        self.id = node_id
        self.channels = channels

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

    def __repr__(self):
        return "<NodeDefinition #{}>".format(self.id)

    def __eq__(self, other):
        return type(self) == type(other) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self.__eq__(other)


def load_definitions_from_yaml(stream):
    data = yaml.safe_load(stream)
    return [NodeDefinition(d['node_id'], d['channels'])
            for d in data]
