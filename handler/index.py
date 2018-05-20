# coding:utf8
import datetime
import socket
import time
import os

import psutil
from tornado.gen import coroutine, Return
from tornado.httpclient import AsyncHTTPClient, HTTPError
from tornado.web import authenticated
from tornado.websocket import WebSocketHandler

from handler import base
from manager import utils
from manager.timerMgr import thread_pool, cycle

SysInfo = []  # {"timestamp": "", "cpu": ""...}
clients = set()
hostname = socket.gethostname()
hostname_ex = ",".join(socket.gethostbyname_ex(socket.gethostname())[2])
process = psutil.Process()
pid = process.pid
cmdline = " ".join(process.cmdline())
curdir = os.path.realpath(os.curdir)

# httpClient = HTTPClient()
# try:
#     url = "http://api.k780.com/?app=ip.local&appkey=10003&sign=b59bc3ef6191eb9f747dd4e83c99f2a4"
#     response = httpClient.fetch(url)
#     ip = "|".join(utils.jsonLoad(response.body)["result"].values())
# except (HTTPError, ValueError, KeyError) as err:
#     # ip = HTTPClient().fetch("http://ltd.qzgame.cc:1009/ip").body
#     response = httpClient.fetch("http://server.5v5.com/ip")
#     ip = response.body


@cycle("系统信息", 3)
@coroutine
def ps():
    if not clients:
        raise Return("NoClient")
    timestamp = time.time()
    cpu_percent = yield thread_pool.submit(psutil.cpu_percent, 0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    net = psutil.net_io_counters()
    if SysInfo:
        interval = timestamp - SysInfo[-1]["timestamp"]
        net_sent_speed = (net.bytes_sent - SysInfo[-1]["net_sent"]) / interval
        net_recv_speed = (net.bytes_recv - SysInfo[-1]["net_recv"]) / interval
    else:
        net_sent_speed = 0
        net_recv_speed = 0
    cpu_process = yield thread_pool.submit(process.cpu_percent, 0.1)
    data = {
            # "hostname": hostname,
            # "hostname_ex": hostname_ex,
            # "ip": ip,
            "timestamp": timestamp,
            "cpu_percent": cpu_percent,
            "cpu_count": psutil.cpu_count(),
            "mem_percent": memory.percent,
            "mem_used": memory.used,
            "mem_total": memory.total,
            "disk_total": disk.total,
            "disk_used": disk.used,
            "disk_percent": disk.percent,
            "net_sent": net.bytes_sent,
            "net_recv": net.bytes_recv,
            "net_sent_speed": net_sent_speed,
            "net_recv_speed": net_recv_speed,
            "cpu_process": cpu_process,
            "mem_process": process.memory_info().rss,
            # "cmdline": process.cmdline(),
            # "pid": process.pid,
            "thread": process.num_threads(),
            "run_time": timestamp - process.create_time(),
            }
    # net = psutil.net_io_counters(pernic=True)
    # interval = timestamp - SysInfo[-1]["timestamp"] if SysInfo else 1
    # for name, now in net.items():
    #     if now.bytes_sent + now.bytes_recv < 1024:
    #         continue
    #     name = name.decode("gbk" if sys.platform.startswith("win") else "utf8")
    #     if SysInfo:
    #         last = SysInfo[-1]["net"].get(name, [0, 0])
    #     else:
    #         last = [now.bytes_sent, now.bytes_recv]
    #     data["net"][name] = [now.bytes_sent,
    #                          now.bytes_recv,
    #                          (now.bytes_sent - last[0]) / interval,
    #                          (now.bytes_recv - last[1]) / interval,
    #                          ]

    SysInfo.append(data)
    if len(SysInfo) > 10:
        SysInfo.pop(0)

    WSHandler.sendSysInfo(data)
    # raise Return(data)
    raise Return("success")


# def bytes2human(n):
#     """
#     :param n:
#     :return:
#     """
#     symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
#     prefix = {}
#     for i, s in enumerate(symbols):
#         prefix[s] = 1 << (i + 1) * 10
#     for s in reversed(symbols):
#         if n >= prefix[s]:
#             value = float(n) / prefix[s]
#             return '%.2f%s' % (value, s)
#     return '%.2fB' % n


def formatByte(num):
    byte = "B"
    for byte in ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y'):
        num /= 1024.0
        if num < 1024:
            break
    return "%.2f%s" % (num, byte)


def formatSysInfo(data):
    sysInfoJson = utils.jsonDump(
        {
         # "hostname": data["hostname"],
         # "hostname_ex": data["hostname_ex"],
         # "ip": data["ip"],
         "timestamp": time.strftime("%H:%M:%S", time.localtime(data["timestamp"])),
         "cpu_percent": "%d%%" % data["cpu_percent"],
         "cpu_count": data["cpu_count"],
         "mem_percent": "%d%%" % data["mem_percent"],
         "mem_used": formatByte(data["mem_used"]),
         "mem_total": formatByte(data["mem_total"]),
         "disk_percent": "%d%%" % data["disk_percent"],
         "disk_used": formatByte(data["disk_used"]),
         "disk_total": formatByte(data["disk_total"]),
         "net_sent": formatByte(data["net_sent"]),
         "net_recv": formatByte(data["net_recv"]),
         "net_sent_speed": formatByte(data["net_sent_speed"])+"/S",
         "net_recv_speed": formatByte(data["net_recv_speed"])+"/S",
         "cpu_process": "%d%%" % data["cpu_process"],
         "mem_process": formatByte(data["mem_process"]),
         # "cmdline": " ".join(data["cmdline"]),
         # "pid": data["pid"],
         "thread": data["thread"],
         "run_time": str(datetime.timedelta(seconds=int(data["run_time"])))
         })
    return sysInfoJson


class IndexHandler(base.BaseHandler):
    # lastTimestamp = time.time()
    # lastNet = psutil.net_io_counters(pernic=True)
    #
    # @authenticated
    # @coroutine
    # def get(self):
    #     cpu = yield thread_pool.submit(psutil.cpu_percent, 0.1)
    #     memory = psutil.virtual_memory()
    #     timestamp = time.time()
    #     nowNet = psutil.net_io_counters(pernic=True)
    #
    #     interval = timestamp - self.lastTimestamp
    #     # nets = {name: [net, self.lastNet.get(name)] for name, net in nowNet.items()}
    #     # if sys.platform.startswith("win"):
    #     #     nets = {key.decode("gbk"): value for key, value in nets.items()}
    #     nets = {}
    #     for name, now in nowNet.items():
    #         if now.bytes_sent == 0 and now.bytes_recv == 0:
    #             continue
    #         last = self.lastNet.get(name)
    #         if sys.platform.startswith("win"):
    #             name = name.decode("gbk")
    #         nets[name] = [bytes2human(now.bytes_sent),
    #                       bytes2human(now.bytes_recv),
    #                       bytes2human((now.bytes_sent-last.bytes_sent)/interval),
    #                       bytes2human((now.bytes_recv-last.bytes_recv)/interval),
    #                       ]
    #         # nets[name] = ["%15s %15s/s" % (bytes2human(now.bytes_sent),
    #         #                                bytes2human((now.bytes_sent-last.bytes_sent)/interval)),
    #         #               "%15s %15s/s" % (bytes2human(now.bytes_recv),
    #         #                                bytes2human((now.bytes_recv - last.bytes_recv) / interval)),
    #         #               ]
    #     self.lastTimestamp = timestamp
    #     self.lastNet = nowNet
    #     import json
    #     data = json.dumps([[time.strftime("%H:%M:%S"), memory.used] for i in range(10, 0, -2)])
    #     print(data)
    #     self.render("index.html", cpu=cpu, memory=memory, nets=nets, interval=interval, timestamp=timestamp)

    # @authenticated
    # @coroutine
    # def post(self):
    #     cpu = yield thread_pool.submit(psutil.cpu_percent, 0.1)
    #     memory = psutil.virtual_memory()
    #     timestamp = time.time()
    #     nowNet = psutil.net_io_counters(pernic=True)
    #
    #     interval = timestamp - self.lastTimestamp
    #     nets = {}
    #     for name, now in nowNet.items():
    #         if now.bytes_sent == 0 and now.bytes_recv == 0:
    #             continue
    #         last = self.lastNet.get(name)
    #         if sys.platform.startswith("win"):
    #             name = name.decode("gbk")
    #         nets[name] = [bytes2human(now.bytes_sent),
    #                       bytes2human(now.bytes_recv),
    #                       bytes2human((now.bytes_sent-last.bytes_sent)/interval),
    #                       bytes2human((now.bytes_recv-last.bytes_recv)/interval),
    #                       ]
    #     self.lastTimestamp = timestamp
    #     self.lastNet = nowNet
    #     result = {"cpu": cpu,
    #               "memory_percent": memory.percent,
    #               "memory_used": memory.used,
    #               "memory_total": memory.total,
    #               "net": nets,
    #               "timestamp": timestamp}
    #     self.write(result)

    @classmethod
    @coroutine
    def getIp(cls):
        try:
            url = "http://api.k780.com/?app=ip.local&appkey=10003&sign=b59bc3ef6191eb9f747dd4e83c99f2a4"
            response = yield AsyncHTTPClient().fetch(url, connect_timeout=1, request_timeout=1)
            ip = "|".join(utils.jsonLoad(response.body)["result"].values())
        except (HTTPError, ValueError, KeyError) as err:
            cls.warning(repr(err))
            response = yield AsyncHTTPClient().fetch("http://server.5v5.com/ip")
            ip = response.body
        raise Return(ip)

    @authenticated
    @coroutine
    def get(self):
        # response = yield AsyncHTTPClient().fetch("http://server.5v5.com/ip")
        # ip = response.body
        # ip = utils.urlopen("http://server.5v5.com/ip").read()
        ip = yield self.getIp()
        self.render("index.html", host=self.request.headers.get("Host"), hostname=hostname, hostname_ex=hostname_ex,
                    ip=ip, pid=pid, cmdline=cmdline, curdir=curdir, log_info=self.log_info)

    @authenticated
    @coroutine
    def post(self):
        self.write(SysInfo[-1])


class WSHandler(WebSocketHandler):
    def open(self):
        clients.add(self)
        # for msg in SysInfo:
        #     self.write_message(msg)
        if SysInfo:
            self.write_message(formatSysInfo(SysInfo[-1]))

    def on_message(self, message):
        self.write_message(u"You said: " + message)

    def on_close(self):
        if self in clients:
            clients.remove(self)

    @staticmethod
    def sendSysInfo(data):
        if not clients:
            return
        msg = formatSysInfo(data)
        for client in clients:
            client.write_message(msg)
