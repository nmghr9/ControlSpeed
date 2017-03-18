# conding:utf-8
import collections
import functools
import threading
import time
import pickle
from controlspeed.local_mutex import LocalMutex, LockError


class ControlSpeed(object):
    def __init__(self, multi=None, max_calls=0, period=1.0, callback=None):
        if period <= 0:
            raise ValueError('Speed limiting period must be > 0')
        if max_calls <= 0:
            raise ValueError('Speed limiting number of calls must be > 0')
        self.multi = multi
        if self.multi:
            self.filename = 'tmp.file'
            self.lock = 'lock.file'

        self.calls = collections.deque()

        self.period = period
        self.max_calls = max_calls
        self.callback = callback

    def __call__(self, f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            with self:
                return f(*args, **kwargs)

        return wrapped

    def __enter__(self):
        self.judge_load()
        if len(self.calls) >= self.max_calls:
            last = self._time_span
            if last >= self.period:
                until = 0
            else:
                until = self.period - last
            if self.callback:
                t = threading.Thread(target=self.callback, args=(until,))
                t.daemon = True
                t.start()
            time.sleep(until)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.calls.append(time.time())
        self.judge_dump()
        while len(self.calls) > self.max_calls:
            self.calls.popleft()
            self.judge_dump()

    @property
    def _time_span(self):
        if self.multi:
            self.load()
        return self.calls[-1] - self.calls[0]

    # will add more mode, threading
    def judge_dump(self):
        if self.multi:
            self.dump()

    def judge_load(self):
        if self.multi:
            self.load()

    def dump(self):
        with LocalMutex(self.lock, wait=True):
            pickle.dump(self.calls, open(self.filename, "w"))

    def load(self):
        with LocalMutex(self.lock, wait=True):
            res = pickle.load(open(self.filename, "r"))
            self.calls = res


class ControlSpeedNetwork(object):
    def __init__(self, redis_conn, key, max_calls=0, period=1.0, callback=None, dynamic=False):
        if period <= 0:
            raise ValueError('Speed limiting period must be > 0')
        if max_calls <= 0:
            raise ValueError('Speed limiting number of calls must be > 0')

        self.mq = MQ(redis_conn, key)
        self.callback = callback
        self.dynamic = dynamic
        self.max_calls_setting = max_calls
        self.period_setting = period

    def __call__(self, f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            with self:
                return f(*args, **kwargs)

        return wrapped

    def __enter__(self):
        if self.mq.llen() >= self.max_calls:
            last = self._time_span
            if last >= self.period:
                until = 0
            else:
                until = self.period - last
            if self.callback:
                t = threading.Thread(target=self.callback, args=(until,))
                t.daemon = True
                t.start()
            time.sleep(until)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.mq.rpush(time.time())
        while self.mq.llen() > self.max_calls:
            self.mq.lpop()

    @property
    def _time_span(self):
        return self.mq.lrange(-1) - self.mq.lrange(0)

    @property
    def _last_point(self):
        return time.time() - self.mq.lrange(-1)

    @property
    def max_calls(self):
        if self.dynamic:
            return self.mq.max_calls
        else:
            return self.max_calls_setting

    @property
    def period(self):
        if self.dynamic:
            return self.mq.period
        else:
            return self.period_setting


class MQ(object):
    def __init__(self, redis_conn, key):
        self.redis_conn = redis_conn
        self.key = key

    def llen(self):
        return self.redis_conn.llen(self.key)

    def rpush(self, item):
        return self.redis_conn.rpush(self.key, item)

    def lpop(self):
        return self.redis_conn.lpop(self.key)

    def lrange(self, offset):
        return float(self.redis_conn.lrange(self.key, offset, offset)[0])

    @property
    def max_calls(self):
        return float(self.redis_conn.get(self.key + '-max-calls') or -1.0)

    @max_calls.setter
    def max_calls(self, value):
        self.redis_conn.set(self.key + '-max-calls', value)

    @property
    def period(self):
        return float(self.redis_conn.get(self.key + '-period') or -1.0)

    @period.setter
    def period(self, value):
        self.redis_conn.set(self.key + '-period', value)


class SpeedSetter(MQ):
    pass
