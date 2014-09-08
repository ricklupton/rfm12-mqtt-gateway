import unittest
from .parser import FrameParser
from .nodes import NodeDefinition


class TestFrameParser(unittest.TestCase):
    def setUp(self):
        nodes = [
            NodeDefinition('bob', 10, 'hh',
                           {'a': {'value': 'x[0]'}, 'b': {'value': '3.0'}}),
            NodeDefinition('joe', 20, 'hh',
                           {'a': {'value': 'x[1]'}, 'b': {'value': '2.1'}}),
            NodeDefinition('fred', 30, 'bl',
                           {'a': {'value': 'x[0]'}, 'b': {'value': 'x[1]'}}),
        ]
        self.parser = FrameParser(nodes)

    def test_it_works(self):
        tests = [
            ('10 34 0 23 0',
             (self.parser.nodes[10], {'a': 34, 'b': 3.0})),

            ('10 135 243 0 0',
             (self.parser.nodes[10], {'a': -3193, 'b': 3.0})),

            ('20 12 0 17 1',
             (self.parser.nodes[20], {'a': 273, 'b': 2.1})),

            ('30 2 17 1 0 0',
             (self.parser.nodes[30], {'a': 2, 'b': 273})),

            (' 30 2\t17 1 0 0\n',
             (self.parser.nodes[30], {'a': 2, 'b': 273})),

            ('> msg', (None, 'msg')),
            ('-> another msg', (None, 'another msg')),
        ]
        for frame, expected in tests:
            self.assertEqual(self.parser.process_frame(frame), expected)

    def test_parse_frame_fails_with_bad_frames(self):
        tests = [
            # Wrong length
            '10 21',
            '10 21 23 32',

            # Non-integer values
            '10 21 aa',
        ]
        for frame in tests:
            with self.assertRaises(ValueError):
                self.parser.process_frame(frame)

    def test_ignores_unknown_nodes(self):
        self.assertEqual(self.parser.process_frame('15 34 0 23 0'), (None, {}))


if __name__ == '__main__':
    unittest.main()
