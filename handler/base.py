# coding:utf8
import logging

from tornado.httputil import urlencode
from tornado.web import RequestHandler
from tornado.gen import coroutine

from manager import utils

class BaseHandler(RequestHandler):
    log_status = 400  # 显示日志级别，根据请求状态200、300...
    paginate = 16  # 分页，单页显示条数

    log_info = {}  # 日志信息{模块:{"time":耗时,"count":请求次数,"exception":异常数,"error":错误数,"warning":警告数}}
    _base_log_info = {"time": 0, "count": 0, "exception": 0, "error": 0, "warning": 0}

    def get_secure_cookie(self, name, value=None, max_age_days=31, min_version=None):
        # result = super(BaseHandler, self).get_secure_cookie(name, value, max_age_days, min_version)
        result = RequestHandler.get_secure_cookie(self, name, value, max_age_days, min_version)
        return result if isinstance(result, str) or not hasattr(result, "decode") else result.decode()

    def get_current_user(self):
        user = {"username": self.get_secure_cookie("username"),
                "email": self.get_secure_cookie("email"),
                "ip": self.get_secure_cookie("ip")}
        return user if user["username"] else None

    def render(_self, template_name, **kwargs):
        kwargs["template"] = template_name
        if "self" in kwargs:
            kwargs.pop("self")

        # 分页链接保留get查询参数
        page_query = urlencode([(k, v[0]) for k, v in _self.request.query_arguments.items() if k != "page"])
        kwargs["page_query"] = "?page=" if len(page_query) == 0 else "?%s&page=" % page_query

        # return super(BaseHandler, _self).render(template_name, **kwargs)  # reload会报错
        return RequestHandler.render(_self, template_name, **kwargs)

    # def get_argument(self, name, default=None, strip=True):
    #     argument = super(BaseHandler, self).get_argument(name, default, strip)
    #     return argument if isinstance(argument, str) or not hasattr(argument, "decode") else argument.decode()

    # log统计
    @classmethod
    def debug(cls, msg, *args, **kwargs):
        return logging.root._log(logging.DEBUG, msg, args, **kwargs)

    @classmethod
    def info(cls, msg, *args, **kwargs):
        return logging.root._log(logging.INFO, msg, args, **kwargs)

    @classmethod
    def warning(cls, msg, *args, **kwargs):
        logInfo = cls.log_info.setdefault("%s.%s" % (cls.__module__, cls.__name__), cls._base_log_info.copy())
        logInfo["warning"] = logInfo.get("warning", 0) + 1
        return logging.root._log(logging.WARNING, msg, args, **kwargs)

    @classmethod
    def error(cls, msg, *args, **kwargs):
        logInfo = cls.log_info.setdefault("%s.%s" % (cls.__module__, cls.__name__), cls._base_log_info.copy())
        logInfo["error"] = logInfo.get("error", 0) + 1
        kwargs["exc_info"] = False
        return logging.root._log(logging.ERROR, msg, args, **kwargs)

    @classmethod
    def exception(cls, msg, *args, **kwargs):
        logInfo = cls.log_info.setdefault("%s.%s" % (cls.__module__, cls.__name__), cls._base_log_info.copy())
        logInfo["exception"] = logInfo.get("exception", 0) + 1
        kwargs["exc_info"] = True
        return logging.root._log(logging.ERROR, msg, args, **kwargs)
    # log统计end

    # 请求log统计
    def _log(self):
        key = self.__class__.__module__ + "." + self.__class__.__name__
        logInfo = self.log_info.setdefault(key, self._base_log_info.copy())
        logInfo["count"] = logInfo.get("count", 0) + 1
        logInfo["time"] = logInfo.get("time", 0) + self.request.request_time()

        # # 屏蔽200、300请求日志
        # if self.get_status() < self.log_status:
        #     if conf.logLevel in ("NOTSET", "DEBUG"):
        #                 logging.debug("%d %s %.2fms", self.get_status(), self._request_summary(),
        #                               1000.0 * self.request.request_time())
        #     return

        # super(BaseHandler, self)._log()
        return RequestHandler._log(self)


class BaseAPIHandler(BaseHandler):
    result = {}

    def initialize(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.result = {"result": False, "code": 0, "message": ""}
        return super().initialize()

    def write_error(self, status_code, **kwargs):
        result = {"result": False, "code": status_code, "message": self._reason}
        self.write(result)
        self.finish()

    def prepare(self):
        # 处理json格式请求参数
        if "application/json" in self.request.headers.get("Content-Type", ""):
            # self.debug("初始化json请求参数:%s", self.request.body)
            try:
                jsonData = utils.jsonLoad(self.request.body)
                for k, v in jsonData.items():
                    if k in self.request.arguments:
                        self.request.arguments[k].append(v)
                    else:
                        self.request.arguments[k] = [v]
            except ValueError as err:
                self.error("初始化json请求参数出错:%s body:%s" % (err, self.request.body))
        return super().prepare()

    @coroutine
    def get(self):
        yield self.post()
