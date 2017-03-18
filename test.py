# coding:utf-8
import time
import redis
from controlspeed import ControlSpeed
from controlspeed import ControlSpeedNetwork

redis_conn = redis.StrictRedis()
key = 'hourong'


@ControlSpeedNetwork(redis_conn, key, max_calls=10, period=3.0)
def do_something(args):
    print(args)
    time.sleep(0.1)


for i in range(20):
    do_something(i)


@ControlSpeed(max_calls=10, period=3.0)
def do_something(args):
    print(args)
    time.sleep(0.1)


for i in range(20):
    do_something(i)

from controlspeed import ControlSpeed

rate = ControlSpeed(max_calls=10, period=3.0)

for i in range(15):
    with rate:
        print(i)


def limited(until):
    duration = int(round(until))
    print('Speed limited, sleeping for %d seconds' % duration)


for i in range(20):
    print(i)

rate = ControlSpeed(max_calls=2, period=3, callback=limited)
for i in range(3):
    with rate:
        print(i)

from controlspeed import SpeedSetter

speed_setter = SpeedSetter(redis_conn, key)
speed_setter.max_calls = 2
speed_setter.period = 2


@ControlSpeedNetwork(redis_conn, key, max_calls=10, period=3.0, dynamic=True)
def do_something(args):
    print(args)
    time.sleep(0.1)


for i in range(40):
    if i == 14:
        speed_setter.max_calls = 8
    do_something(i)
