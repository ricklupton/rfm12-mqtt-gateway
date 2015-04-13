import argparse
import logging
import asyncio
from rfm12_mqtt_gateway.gateway import EmonMQTTGateway


def main():
    # Set up logging
    parser = argparse.ArgumentParser(description='emon gateway')
    parser.add_argument('-L', '--log-level', default='warning')
    args = parser.parse_args()

    numeric_level = getattr(logging, args.log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % args.log_level)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s %(name)s [%(levelname)s] %(message)s")
    logging.getLogger('asyncio').setLevel('WARNING')

    gateway = EmonMQTTGateway()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(gateway.run_input())
    loop.close()


if __name__ == '__main__':
    main()
