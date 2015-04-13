import unittest
from unittest.mock import Mock
from rfm12_mqtt_gateway.parser import FrameParser
from rfm12_mqtt_gateway.nodes import NodeDefinition


class TestFrameParser(unittest.TestCase):
    def setUp(self):
        nodes = [
            NodeDefinition('bob', 10, 'hh'),
            NodeDefinition('joe', 20, 'hh'),
            NodeDefinition('fred', 30, 'bl'),
        ]
        for n in nodes:
            n.parse_payload = Mock()
        self.parser = FrameParser(nodes)

    def test_frames_dispatched_to_nodes(self):
        self.parser.process_frame('10 34 0 23 0')
        self.parser.nodes[10].parse_payload.assert_called_once_with(
            bytes((34, 0, 23, 0)))
        self.assertFalse(self.parser.nodes[20].parse_payload.called)
        self.assertFalse(self.parser.nodes[30].parse_payload.called)

        self.parser.process_frame('20 12 0 17 1')
        self.parser.nodes[20].parse_payload.assert_called_once_with(
            bytes((12, 0, 17, 1)))
        self.assertFalse(self.parser.nodes[30].parse_payload.called)

    def test_messages_are_discarded(self):
        tests = [
            ('> msg', (None, 'msg')),
            ('-> another msg', (None, 'another msg')),
        ]
        for frame, expected in tests:
            self.assertEqual(self.parser.process_frame(frame), expected)

    def test_parse_frame_fails_with_bad_frames(self):
        tests = [
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
