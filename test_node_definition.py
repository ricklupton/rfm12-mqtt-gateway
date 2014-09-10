import unittest
from .nodes import NodeDefinition, load_definitions_from_yaml

TEST_YAML = """
- node_id: 10
  name: /home/electricity
  payload: hhh
  channels:
    value1:
      value: x[0]
      units: m
    value2:
      value: 2 * x[1] - x[2]
      units: deg/s
      description: Long description
    value3:
      value: 6.1
  commands:
    set_time:
      payload: bbbb
      values: "[0, x['hours'], x['minutes'], x['seconds']]"
"""

TEST_CHANNELS = {
    'value1': {'value': 'x[0]',
               'units': 'm'},
    'value2': {'value': '2 * x[1] - x[2]',
               'units': 'deg/s',
               'description': 'Long description'},
    'value3': {'value': '6.1'},
}

TEST_COMMANDS = {
    'set_time': {'payload': 'bbbb',
                 'values': "[0, x['hours'], x['minutes'], x['seconds']]"},
}


class TestNodeDefinition(unittest.TestCase):
    def setUp(self):
        self.node = NodeDefinition('name', 10, 'hhh',
                                   TEST_CHANNELS, TEST_COMMANDS)

    def test_it_can_be_created(self):
        self.assertEqual(self.node.payload_format, 'hhh')
        self.assertEqual(self.node.channels, TEST_CHANNELS)
        self.assertEqual(self.node.commands, TEST_COMMANDS)

    def test_parse_payload_works(self):
        tests = [
            (bytes((34, 0, 23, 0, 1, 0)),
             {'value1': 34, 'value2': 2 * 23 - 1, 'value3': 6.1}),

            (bytes((135, 243, 0, 0, 0, 0)),
             {'value1': -3193, 'value2': 0, 'value3': 6.1}),
        ]
        for payload, expected in tests:
            self.assertEqual(self.node.parse_payload(payload), expected)

    def test_parse_payload_fails_with_bad_frames(self):
        tests = [
            # Wrong length
            bytes((10,)),
            bytes((10, 21, 23, 32)),
        ]
        for frame in tests:
            with self.assertRaises(ValueError):
                self.node.parse_payload(frame)

    def test_parse_values_works(self):
        values = [2.3, 4.3, 6.4, 3.2]
        result = self.node.parse_values(values)
        self.assertEqual(set(result.keys()),
                         set(['value1', 'value2', 'value3']))
        self.assertEqual(result, {
            'value1': 2.3,
            'value2': 2 * 4.3 - 6.4,
            'value3': 6.1,
        })

    def test_parse_values_cannot_access_namespace(self):
        node = NodeDefinition('bob', 66, 'h', {'bad': {'value': 'unittest'}})
        with self.assertRaises(RuntimeError):
            node.parse_values([1, 2, 3])

    def test_parse_values_raises_ValueError_if_not_enough_values(self):
        node = NodeDefinition('bob', 66, 'h', {'name': {'value': 'x[4]'}})
        with self.assertRaises(ValueError):
            node.parse_values([1, 2, 3])

    def test_encode_command_works(self):
        tests = [
            ('bbbb', "[0, x['hours'], x['minutes'], x['seconds']]",
             {'hours': 12, 'minutes': 21, 'seconds': 59},
             bytes((0, 12, 21, 59))),

            (' b b 5s', "[0, 5, x['message'].encode('ascii')]",
             {'message': 'hello'},
             bytes([0, 5]) + b'hello'),
        ]
        for payload, pattern, values, expected in tests:
            node = NodeDefinition('name', 1, 'b', commands={
                'cmd': {'payload': payload, 'values': pattern}
            })
            self.assertEqual(node.encode_command('cmd', values),
                             expected)

    def test_encode_command_cannot_access_namespace(self):
        node = NodeDefinition('bob', 66, 'h', commands={
            'bad': {'payload': 'b', 'values': 'unittest'}
        })
        with self.assertRaises(RuntimeError):
            node.encode_command('bad', {})

    def test_encode_command_raises_ValueError_if_not_enough_values(self):
        node = NodeDefinition('bob', 66, 'h', commands={
            'name': {'payload': 'b', 'values': 'x[4]'}
        })
        with self.assertRaises(ValueError):
            node.encode_command('name', [1, 2, 3])

    def test_comparisons(self):
        self.assertEqual(
            NodeDefinition('bob', 10, 'h', {'name': {'value': '1'}}),
            NodeDefinition('bob', 10, 'h', {'name': {'value': '1'}})
        )
        self.assertNotEqual(
            NodeDefinition('bob', 10, 'h', {'name': {'value': '1'}}),
            NodeDefinition('bob', 11, 'h', {'name': {'value': '1'}})
        )
        self.assertNotEqual(
            NodeDefinition('bob', 10, 'h', {'name': {'value': '1'}}),
            NodeDefinition('bob', 10, 'h', {'name': {'value': '2'}})
        )

    def test_repr(self):
        self.assertEqual(repr(NodeDefinition('fred', 10, 'h', {})),
                         '<NodeDefinition #10 fred>')


class TestNodeDefinitionsFromYaml(unittest.TestCase):
    def test_loading_from_yaml(self):
        nodes = load_definitions_from_yaml(TEST_YAML)
        self.assertEqual(nodes, [
            NodeDefinition('/home/electricity', 10, 'hhh',
                           TEST_CHANNELS, TEST_COMMANDS)
        ])
