# ControlSpeed
 
因个人需要，对 ControlSpeedNetwork 部分以及 MQ 进行了修改，可以通过读取 redis 中的 max-calls 和 period 进行动态设置任务的速度，可以在任务执行的过程中通过自己，或另一跟程序改变任务的速度以控制。

使用方法如下：

```python
import redis
import time
from controlspeed import SpeedSetter,ControlSpeedNetwork

redis_conn = redis.StrictRedis()
key = 'hourong'

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

```

以下为原版的 README

# ControlSpeed  
这项目是用来控制函数调用的频率, 不仅支持本地的同步线程模式, 而且支持分布式模式.   
[更多开发描述,请点击链接](http://xiaorui.cc)

ControlSpeed(本地版)还不兼容多线程的场景, 当然你可以用ControlSpeedNetwork分布式版解决. 缺点是每次访问都会有一次网络io消耗.  

version 2.3:  
1. Add multiprocessing mode support

#Usage:

装饰器使用方法
```
from controlspeed import ControlSpeed
@ControlSpeed(max_calls=10, period=1.0)
def do_something():
    pass
```

with关键词控制上下文
```
from controlspeed import ControlSpeed
rate = ControlSpeed(max_calls=10, period=1.0)
for i in range(100):
    with rate:
        do_something()
```

支持回调函数的控速
```
from controlspeed import ControlSpeed
import time
def limited(until):
    duration = int(round(until - time.time()))
    print 'Speed limited, sleeping for %d seconds' % duration

rate = ControlSpeed(max_calls=2, period=3, callback=limited)
for i in range(3):
    with rate:
        print i
```

在2.1加入了分布式限频, 借助于redis实现.
```
import redis
redis_conn = redis.StrictRedis()
key = 'xiaorui.cc'

@ControlSpeedNetwork(redis_conn, key, max_calls=10, period=3.0)
def do_something(args):
    print args
    time.sleep(0.1)

for i in xrange(20):
    do_something(i)
```
