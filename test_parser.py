import unittest
from .parser import _parse_frame, FrameParser
from .nodes import NodeDefinition


class TestParseFrameFunction(unittest.TestCase):
    def test_parse_frame(self):
        tests = [
            ('32 34 0', (32, [34])),
            ('  32  34\t0\t', (32, [34])),
            ('32 135 243 21 1', (32, [-3193, 277])),
            ('> message text', (None, 'message text')),
            ('>', (None, '')),
            ('-> another message  ', (None, 'another message')),
        ]
        for frame, expected in tests:
            self.assertEqual(_parse_frame(frame), expected)

    def test_parse_frame_fails_with_wrong_length(self):
        tests = [
            '10',
            '10 21',
            '10 21 23 32',
        ]
        for frame in tests:
            with self.assertRaises(ValueError):
                _parse_frame(frame)

    def test_parse_frame_fails_with_non_integers(self):
        tests = [
            '10 21 aa',
        ]
        for frame in tests:
            with self.assertRaises(ValueError):
                _parse_frame(frame)


class TestFrameParser(unittest.TestCase):
    def setUp(self):
        nodes = [
            NodeDefinition(10, {'a': {'value': 'x[0]'}, 'b': {'value': '3.0'}}),
            NodeDefinition(20, {'a': {'value': 'x[1]'}, 'b': {'value': '2.1'}}),
        ]
        self.parser = FrameParser(nodes)

    def test_it_works(self):
        tests = [
            ('10 34 0 23 0', (self.parser.nodes[10], {'a': 34, 'b': 3.0})),
            ('20 12 0 17 1', (self.parser.nodes[20], {'a': 273, 'b': 2.1})),
        ]
        for frame, expected in tests:
            self.assertEqual(self.parser.process_frame(frame), expected)

    def test_ignores_messages(self):
        self.assertEqual(self.parser.process_frame('> message'), (None, {}))

    def test_ignores_unknown_nodes(self):
        self.assertEqual(self.parser.process_frame('15 34 0 23 0'), (None, {}))


if __name__ == '__main__':
    unittest.main()
