# coding:utf8
import logging

import tornado.log
import tornado.web
from tornado.websocket import WebSocketHandler
from tornado.gen import coroutine
from tornado.web import authenticated

import conf
from handler import base

clients = set()
msgs = []
logger = logging.getLogger()
formatter = tornado.log.LogFormatter()


# class LogFilter(logging.Filter):
#     def filter(self, record):
#         # level = record.levelno
#         msg = formatter.format(record)
#         msgs.append(msg)
#         if len(msgs) > 1000:
#             msgs.pop(0)
#         for client in Clients:
#             client.write_message(msg)
#         return super(LogFilter, self).filter(record)
#
#
# # 如果reload就删除旧的
# for i in logger.filters:
#     if i.__class__.__name__ == "LogFilter":
#         logger.removeFilter(i)
#
# # 添加新
# logger.addFilter(LogFilter())
# tornado.log.gen_log.addFilter(LogFilter())
# tornado.log.app_log.addFilter(LogFilter())
# tornado.log.access_log.addFilter(LogFilter())


class LoggingHandler(logging.Handler):
    def handle(self, record):
        msg = formatter.format(record)
        msgs.append(msg)
        if len(msgs) > 1000:
            msgs.pop(0)
        for client in clients:
            client.write_message(msg)


# 如果reload就删除旧的
for logHandler in logger.handlers:
    # print(handler, handler.__class__.__name__ == "LoggingHandler")
    if logHandler.__class__.__name__ == "LoggingHandler":
        logger.removeHandler(logHandler)
# 添加新
logger.addHandler(LoggingHandler())


class LogHandler(base.BaseHandler):
    @tornado.web.authenticated
    def get(self):
        if self.get_argument("test", False):
            logging.debug("debug")
            logging.info("info")
            logging.warning("warning")
            logging.error("err")
            logging.fatal("fatal")
        self.render('log.html', host=self.request.headers.get("Host"), level=logging.getLevelName(conf.logLevel))

    def post(self):
        level = int(self.get_argument("level"))
        # if not hasattr(logging, level.upper()):
        #     return self.write({"result": False, "level": level, "msg": "错误的日志等级"})
        # logger.setLevel(getattr(logging, level.upper()))

        tornado.log.access_log.setLevel(level)
        tornado.log.app_log.setLevel(level)
        tornado.log.gen_log.setLevel(level)
        logger.setLevel(level)

        conf.logLevel = logging.getLevelName(level)

        logger.log(level, "logging级别:%s" % conf.logLevel)
        self.write({"result": True, "level": level})


class WSHandler(WebSocketHandler):
    def open(self):
        clients.add(self)
        # for msg in msgs:
        #    self.write_message(msg)
        self.write_message("\r\n".join(msgs))

    def on_message(self, message):
        self.write_message(u"You said: " + message)

    def on_close(self):
        if self in clients:
            clients.remove(self)


class Handler(base.BaseHandler):
    @authenticated
    @coroutine
    def get(self):
        self.render("handler.html", log_info=self.log_info)
