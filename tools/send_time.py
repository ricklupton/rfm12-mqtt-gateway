import paho.mqtt.publish as publish
from datetime import datetime
import json

now = datetime.now()
payload = dict(hours=now.hour, minutes=now.minute, seconds=now.second)

msgs = [
    {'topic':   '/send_command/home/livingroom/set_time',
     'payload': json.dumps(payload)},
]

publish.multiple(msgs, hostname="localhost")
