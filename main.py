# coding:utf8
from __future__ import unicode_literals, division, print_function

import importlib
import logging
import sys

import tornado.escape
from tornado.ioloop import IOLoop
from tornado.options import define, options
from tornado.web import RequestHandler, Application

import conf
import url
from manager import timerMgr, utils


# http://127.0.0.1:8000/reload/conf
class ReloadHandler(RequestHandler):
    log_handler = 200

    def get(self, moduleName):
        _module = importlib.import_module(moduleName)
        # logging.info("reload:%r" % importlib.reload(_module))

        # 兼容py2、3
        if hasattr(importlib, "reload"):
            _reload = importlib.reload
        else:
            _reload = importlib.import_module('__builtin__').reload
        logging.info("reload:%r" % _reload(_module))

        server.__init__()
        self.write({"result": True, "msg": "reload成功"})


class Server(Application):
    def __init__(self):
        super(Server, self).__init__(url.urls(ReloadHandler), **conf.settings)

    """屏蔽200、300请求日志，方法3，每个handler可自行控制是否显示"""
    def log_request(self, log_handler):
        # if log_handler.get_status() < 300:
        #     log_method = logging.debug
        # elif log_handler.get_status() < 400:
        #     log_method = logging.info
        # elif log_handler.get_status() < 500:
        #     log_method = logging.warning
        # else:
        #     log_method = logging.error
        # request_time = 1000.0 * log_handler.request.request_time()
        # log_method("%d %s %.2fms", log_handler.get_status(),
        #            log_handler._request_summary(), request_time)
        if log_handler.get_status() < getattr(log_handler, "log_status", 400):
            if conf.logLevel in ("NOTSET", "DEBUG"):
                logging.debug("%d %s %.2fms", log_handler.get_status(), log_handler._request_summary(),
                              1000.0 * log_handler.request.request_time())
            return
        super(Server, self).log_request(log_handler)


# 屏蔽200、300请求日志
# logging.getLogger("tornado.access").setLevel(logging.WARNING)  # 方法1
# def log_function(log_handler):
#     if log_handler.get_status() < getattr(log_handler, "log_status", 400):
#         return
#     if log_handler.get_status() < 400:
#         log_method = logging.info
#     elif log_handler.get_status() < 500:
#         log_method = logging.warning
#     else:
#         log_method = logging.error
#     request_time = 1000.0 * log_handler.request.request_time()
#     log_method("%d %s %.2fms", log_handler.get_status(), log_handler._request_summary(), request_time)
# conf.settings["log_function"] = log_function  # 方法2，每个handler可自行控制是否显示


class StreamHandler(logging.StreamHandler):
    """pycharm控制台颜色"""
    def emit(self, record):
        self.stream = sys.stdout if record.levelno < logging.ERROR else sys.stderr
        super(StreamHandler, self).emit(record)


if conf.settings.get("debug"):
    logging.StreamHandler = StreamHandler


# class LogFormatter(tornado.log.LogFormatter):
#     """日志中的模块修改为文件路径，方便调试跳转"""
#     # DEFAULT_FORMAT = tornado.log.LogFormatter.DEFAULT_FORMAT + '\nFile "%(pathname)s", line %(lineno)d'
#     # DEFAULT_FORMAT = '[%(levelname)1.1s %(asctime)s File "%(relativePath)s", line %(lineno)d] %(message)s'
#     DEFAULT_FORMAT = '[%(levelname)1.1s %(asctime)s %(path)s] %(message)s'
#
#     def __init__(self, fmt=DEFAULT_FORMAT, datefmt=tornado.log.LogFormatter.DEFAULT_DATE_FORMAT,
#                  style='%', color=True, colors=tornado.log.LogFormatter.DEFAULT_COLORS):
#         super(LogFormatter, self).__init__(fmt, datefmt, style, color, colors)
#
#     def format(self, record):
#         # record.relativePath = os.path.relpath(record.pathname)
#
#         # try:
#         #     record.path = 'File "%s", line %d' % (os.path.relpath(record.pathname), record.lineno)
#         # except ValueError:
#         #     record.path = '%s:%d' % (record.module, record.lineno)
#
#         if os.path.splitdrive(record.pathname)[0] != os.path.splitdrive(os.path.abspath("."))[0] or \
#                 len(os.path.relpath(record.pathname)) > len(record.pathname):
#             record.path = '%s:%d' % (record.module, record.lineno)
#         else:
#             record.path = 'File "%s", line %d' % (os.path.relpath(record.pathname), record.lineno)
#
#         return super(LogFormatter, self).format(record)
#
#
# # 日志中的模块修改为文件路径，方便调试跳转
# if conf.settings.get("debug"):
#     tornado.log.LogFormatter = LogFormatter


# 修复escape.json_encode同时传入bytes和str报错
tornado.escape.json_encode = lambda msg: utils.jsonDump(msg).replace("</", "<\\/")

# 日志等级，如果没有--logging参数，就使用conf里面的loglevel
if not any(argv.startswith("--logging") for argv in sys.argv):
    sys.argv.append("--logging=%s" % conf.logLevel)

define("port", default=8000, help="run on the given port", type=int)
options.parse_command_line()
server = Server()

if __name__ == "__main__":
    # 多进程模式，不推荐
    if conf.process:
        import tornado.netutil
        import tornado.process
        import tornado.httpserver
        sockets = tornado.netutil.bind_sockets(options.port)
        tornado.process.fork_processes(conf.process if isinstance(conf.process, int) else 0)
        httpServer = tornado.httpserver.HTTPServer(server)
        httpServer.add_sockets(sockets)
    else:
        # 单进程
        server.listen(options.port)

    timerMgr.initIOLoop()
    print("Tornado is running on http://127.0.0.1:%d" % options.port)
    IOLoop.instance().start()
