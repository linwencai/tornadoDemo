# coding:utf8
"""
定时器，支持函数和协程

# 示例1，周期调用一个函数
@Cycle.deco(1)
def func():
    return "success"

# 示例2，定时调用一个协程
@Cron.deco("*/2")
@tornado.gen.coroutine
def coroutine():
    raise tornado.gen.Return("success“)
"""
import logging
import time

import tornado.ioloop
from concurrent.futures import ThreadPoolExecutor  # py3标准库，py2:pip install futures
from tornado.concurrent import Future

import conf

thread_pool = ThreadPoolExecutor(conf.threads)

# 调用阻塞函数
# @gen.coroutine
# def call_blocking():
#     yield thread_pool.submit(blocking_func, args)


class _Cycle(tornado.ioloop.PeriodicCallback):
    """
    间隔调用定时器
    """
    def __init__(self, _name, _func, _interval, isStart, *_args, **_kwargs):
        self.id = hash(_func)
        self.name = _name
        self.lastStartTime = 0  # 上一次运行时间
        self.lastEndTime = 0  # 上一次运行结束时间
        self.result = None  # 上一次运行结果
        self.func = _func    # 函数
        self.args = _args    # 函数的实参
        self.kwargs = _kwargs    # 函数的实参
        self.count = 0  # 运行次数
        self.isStart = isStart  # 是否启动，否则需要手动启动

        # io_loop=True防止多进程模式报错
        super(_Cycle, self).__init__(self.run, _interval, io_loop=True)
        self.io_loop = tornado.ioloop.IOLoop.current(False)
        if isStart and self.io_loop:
            self.start()

        # super(_Cycle, self).__init__(self.run, _interval)
        return

    def __str__(self):
        return "%s(%s)" % (self.name, self.callback_time//1000)

    def start(self):
        # 防止同时启动多个定时器
        if self.is_running():
            return

        # 防止多进程模式报错
        # self.io_loop = tornado.ioloop.IOLoop.current(False)
        if self.io_loop is True:
            return

        return super(_Cycle, self).start()

    @classmethod
    def deco(cls, _name, _interval, _isStart=True, *_args, **_kwargs):
        """
        装饰器
        :param _name: 定时器名字
        :param _interval: 间隔秒
        :param _isStart: 是否开始定时器
        :return: func
        """
        def wrapper(func):
            timer = cls(_name, func, _interval * 1000, _isStart, *_args, **_kwargs)
            if _name in timerDict:
                timerDict[_name].stop()
            timerDict[_name] = timer
            return func
        return wrapper

    def run(self, isStart=False):
        """
        定时调用的方法
        :param isStart: 是否立即执行
        :return:
        """
        if isinstance(self.result, Future) and self.result.running() and not isStart:
            logging.error("Cycle Future:%s is running:%ss" % (self.func.__name__, time.time()-self.lastStartTime))
            return

        self.lastStartTime = time.time()
        try:
            result = self.func(*self.args, **self.kwargs)
        except BaseException as err:
            result = "Error:%r" % err
            # logging.error("Cycle func:%s %s" % (self.func.__name__, result), exc_info=1)
            logging.exception("Cycle func:%s %s" % (self.func.__name__, result))

        self.lastEndTime = time.time()
        self.result = result
        if isinstance(result, Future):
            result.add_done_callback(self.futureCallBack)
        self.count += 1
        return

    def futureCallBack(self, future):
        """
        future的结果回调方法
        :param future:
        :return:
        """
        try:
            result = future.result()
        except Exception as err:
            result = "Future Error:%r" % err
            # logging.error("Callback:%s %s" % (self.func.__name__, result), exc_info=1)
            logging.exception("Callback:%s %s" % (self.func.__name__, result))
        self.lastEndTime = time.time()
        self.result = result
        return


class _Cron(_Cycle):
    """
    cron定时器
    """
    def __init__(self, _name, _callback, _second, _minute, hour, _weekday, isStart, *_args, **_kwargs):
        self.second = self.getCron(_second, range(60))
        self.minute = self.getCron(_minute, range(60))
        self.hour = self.getCron(hour, range(24))
        self.weekday = self.getCron(_weekday, range(7))
        self.cronStr = "{} {} {} {}".format(_second, _minute, hour, _weekday)
        self.lastCheckTime = time.time()
        super(_Cron, self).__init__(_name, _callback, 1000, isStart, *_args, **_kwargs)

    def __str__(self):
        return "%s(%s)" % (self.name, self.cronStr)

    @classmethod
    def deco(cls, _name, _second="*", _minute="*", _hour="*", _weekday="*", _isStart=True, *_args, **_kwargs):
        """
        装饰器
        :param _name: 定时器名字
        :param _second: 0-59 , - * /
        :param _minute: 0-59 , - * /
        :param _hour: 0-59 , - * /
        :param _weekday: 0-6 , - * /
        :param _isStart: 是否开始定时器
        :return: func
        """
        def wrapper(func):
            timer = cls(_name, func, _second, _minute, _hour, _weekday, _isStart, *_args, **_kwargs)
            if _name in timerDict:
                timerDict[_name].stop()
            timerDict[_name] = timer
            return func
        return wrapper

    @staticmethod
    def getCron(value, limit):
        """
        根据cron的值，获取对应的时间的集合
        :param value: cron的值
        :param limit: 时间范围
        :return: 时间的集合
        """
        if value == "*":
            # result = set(limit)
            result = True  # 提高性能
        elif isinstance(value, int):
            # result = {value}
            result = [value]  # 兼容py26
        elif value.isdigit():
            # result = {int(value)}
            result = [int(value)]  # 兼容py26
        elif value.startswith("*/"):
            num = int(value.strip("*/"))
            result = set(i for i in limit if i % num == 0)
        elif "," in value:
            result = set(int(i) for i in value.split(",") if i.isdigit())
        elif "-" in value:
            start, end = value.split("-")
            result = set(range(int(start), int(end) + 1))
        else:
            raise Exception("无效的cron值:%s" % value)
        return result

    def isInTime(self, timestamp):
        """
        是否在时间段内内
        :param timestamp:
        :return:
        """
        timetuple = time.localtime(timestamp)
        return ((self.second is True or timetuple.tm_sec in self.second) and
                (self.minute is True or timetuple.tm_min in self.minute) and
                (self.hour is True or timetuple.tm_hour in self.hour) and
                (self.weekday is True or timetuple.tm_wday in self.weekday))

    def checkTime(self, timestamp):
        """
        检查时间，遍历上次到本次的每一秒，如果有符合时间就执行函数
        :param timestamp:
        :return:
        """
        lastCheckTime = self.lastCheckTime
        self.lastCheckTime = timestamp
        if lastCheckTime == 0 or lastCheckTime - timestamp < 2:
            return self.isInTime(timestamp)
        else:
            timeRange = range(int(lastCheckTime), int(timestamp))
            for timestamp in timeRange:
                if self.isInTime(timestamp + 1):
                    return True
            return False

    def run(self, isStart=False):
        """
        定时调用的方法
        :param isStart: 是否立即执行
        :return:
        """
        timestamp = time.time()
        if not self.checkTime(timestamp) and not isStart:
            return

        if isinstance(self.result, Future) and self.result.running() and not isStart:
            logging.error("Cron Future:%s is running:%ss" % (self.func.__name__, timestamp-self.lastStartTime))
            return

        self.lastStartTime = timestamp
        try:
            result = self.func(*self.args, **self.kwargs)
        except Exception as err:
            result = "Error:%r" % err
            # logging.error("Cron func:%s %s" % (self.func.__name__, result), exc_info=1)
            logging.exception("Cron func:%s %s" % (self.func.__name__, result))

        self.lastEndTime = time.time()
        self.result = result
        if isinstance(result, Future):
            result.add_done_callback(self.futureCallBack)
        self.count += 1
        return


class TimerDict(dict):
    """
    全局定时器字典 {func: timer}
    重载部分方法和操作符，防止timer内存泄漏
    """
    def stopTimer(self, k, v=None):
        v = v or self.get(k)
        if v and hasattr(v, "stop"):
            v.stop()
        return bool(v)

    def setdefault(self, k, d=None):
        self.stopTimer(k)
        return super(TimerDict, self).setdefault(k, d)

    def __setitem__(self, k, v):
        self.stopTimer(k)
        return super(TimerDict, self).__setitem__(k, v)

    def __delitem__(self, k):
        self.stopTimer(k)
        return super(TimerDict, self).__delitem__(k)

    def pop(self, k, d=None):
        self.stopTimer(k)
        return super(TimerDict, self).pop(k, d)

    def popitem(self):
        item = super(TimerDict, self).popitem()
        self.stopTimer(*item)
        return item

    def getById(self, timerId, default=None):
        for timer in self.values():
            if timer.id == timerId:
                return timer
        return default


timerDict = TimerDict()
cycle = _Cycle.deco
cron = _Cron.deco


def stopAll():
    for timer in timerDict.values():
        timer.stop()
    return


def startAll():
    for timer in timerDict.values():
        timer.start()
    return


# 初始化IOLoop(tornado多进程模式，不能提前初始化IOLoop)
def initIOLoop():
    for timer in timerDict.values():
        timer.io_loop = tornado.ioloop.IOLoop.current()
        if timer.isStart:
            timer.start()
    return


if __name__ == "__main__":
    def test1():
        import tornado.gen
        import tornado.concurrent
        from tornado.httpclient import AsyncHTTPClient

        index = [0]

        @cycle("测试1", 2)
        @tornado.gen.coroutine
        def f1():
            print("in:", time.localtime().tm_sec)
            # # 挂起测试
            # yield tornado.gen.sleep(1)
            # time.sleep(2)
            # result = tornado.gen.Return("abc")

            # 异步网络请求，模拟耗时0.1秒的请求
            response = yield AsyncHTTPClient().fetch("http://10.163.254.246:8000/3.1")
            timerDict["测试1"].stop()  # 停止当前定时器，防止覆盖future
            result = tornado.gen.Return(response.body)
            # 异步网络请求end

            # # 异常测试
            # result = 1//0

            print("out:", time.localtime().tm_sec)
            raise result

        @cycle("测试2", 1, a=u"参数测试")
        def f2(a):
            index[0] += 1
            if index[0] > 3:
                io_loop.stop()

            # 结果打印
            # for k,v in timerDict.items():
            #     print("{0}:{1} {2} {3}".format(id(k), id(v[0]), v[1:3], id(v[-1])))
            print(index[0], a, timerDict["测试1"].result)

            # 内存溢出测试
            # del timerDict["测试1"]
            # cycle("测试3", 2000)(f1)
            # 内存溢出测试end

            return index[0]
    test1()

    def test2():
        for cronInfo in ["*", 2, "3", "*/4", "5,6,7,8,9,10"]:
            import tornado.gen

            @cron("cron测试1", cronInfo, name=cronInfo)
            @tornado.gen.coroutine
            def f1(name):
                print(name, time.localtime().tm_sec)
                # raise Exception("test")
                yield tornado.gen.sleep(2)
                raise tornado.gen.Return(123)
    test2()

    io_loop = tornado.ioloop.IOLoop.current()
    io_loop.start()
