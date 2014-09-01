import unittest
from .nodes import NodeDefinition, load_definitions_from_yaml

TEST_YAML = """
- node_id: 10
  channels:
    value1:
      value: x[0]
      units: m
    value2:
      value: 2 * x[1] - x[2]
      units: deg/s
      description: Long description
"""

TEST_CHANNELS = {
    'value1': {'value': 'x[0]',
               'units': 'm'},
    'value2': {'value': '2 * x[1] - x[2]',
               'units': 'deg/s',
               'description': 'Long description'},
}


class TestNodeDefinition(unittest.TestCase):
    def setUp(self):
        self.node = NodeDefinition(10, TEST_CHANNELS)

    def test_it_can_be_created(self):
        self.assertEqual(self.node.channels, TEST_CHANNELS)

    def test_parses_values(self):
        values = [2.3, 4.3, 6.4, 3.2]
        result = self.node.parse_values(values)
        self.assertEqual(set(result.keys()), set(['value1', 'value2']))
        self.assertEqual(result, {
            'value1': 2.3,
            'value2': 2 * 4.3 - 6.4,
        })

    def test_cannot_access_namespace(self):
        node = NodeDefinition(66, {'bad': {'value': 'unittest'}})
        with self.assertRaises(RuntimeError):
            node.parse_values([1, 2, 3])

    def test_raises_ValueError_if_not_enough_values(self):
        node = NodeDefinition(66, {'name': {'value': 'x[4]'}})
        with self.assertRaises(ValueError):
            node.parse_values([1, 2, 3])

    def test_comparisons(self):
        self.assertEqual(NodeDefinition(10, {'name': {'value': '1'}}),
                         NodeDefinition(10, {'name': {'value': '1'}}))
        self.assertNotEqual(NodeDefinition(10, {'name': {'value': '1'}}),
                            NodeDefinition(11, {'name': {'value': '1'}}))
        self.assertNotEqual(NodeDefinition(10, {'name': {'value': '1'}}),
                            NodeDefinition(10, {'name': {'value': '2'}}))

    def test_repr(self):
        self.assertEqual(NodeDefinition(10, {}), '<NodeDefinition #10>')


class TestNodeDefinitionsFromYaml(unittest.TestCase):
    def test_loading_from_yaml(self):
        nodes = load_definitions_from_yaml(TEST_YAML)
        self.assertEqual(nodes, [NodeDefinition(10, TEST_CHANNELS)])
