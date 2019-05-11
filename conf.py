# coding:utf8
from __future__ import unicode_literals
import os
import socket
# import sys
import logging.config

port = 8000
logLevel = "INFO"  # 日志等级 NOTSET|DEBUG|INFO|WARNING|ERROR

process = False  # 多进程模式 {True:根据cpu核心数，数字:子进程数，False:单进程}
# process = not sys.platform.startswith("win")  # 多进程模式，根据平台
threads = 16  # 线程池数量

# os.chdir(os.path.dirname(os.path.dirname(__file__)))  # 修改工作目录

settings = {
    # "static_path": os.path.join(os.path.dirname(__file__), "static"),
    # "template_path": os.path.join(os.path.dirname(__file__), "templates"),
    "static_path": os.path.join(os.curdir, "static"),
    "template_path": os.path.join(os.curdir, "templates"),
    "cookie_secret": "61oETzKX1AGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
    "login_url": "/login",  # 登录页面
    # "xsrf_cookies": True,  # 防止跨域攻击
    "debug": True,
    "compiled_template_cache": False,  # 缓存模板
    "static_hash_cache": False,  # 缓存静态文件
    "autoreload": False,  # 自动重启
    "serve_traceback": False,  # 捕获handler的异常
    "xheaders": True,  # 使用header中的X-Real-IP
}


# log路径
logFileDir = os.path.join(".", "log")  # log文件的目录
not os.path.exists(logFileDir) and os.mkdir(logFileDir)
logFilePath = os.path.join(logFileDir, "server.log")

# log配置字典
LOGGING_DIC = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '[%(levelname)s %(asctime)s %(module)s:%(lineno)d] %(message)s',
            'datefmt': '%Y%m%d %H:%M:%S',
        },
        'simple': {
            'format': '[%(levelname)1.1s %(asctime)s %(module)s:%(lineno)d] %(message)s',
            'datefmt': '%H:%M:%S',
        },
    },
    'handlers': {
        # 打印到终端的日志
        'console': {
            'level': logLevel,
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
        'default': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'formatter': 'standard',
            'filename': logFilePath,  # 日志文件
            'when': 'midnight',  # 间隔：每天的凌晨
            'encoding': 'utf-8',  # 日志文件的编码
            'backupCount': 10,  # 保留10份日志
        },
    },
    'root': {
        'handlers': ['default', 'console'],
        'level': 'DEBUG',
        # 'propagate': True,  # 向上（更高level的logger）传递
    },
}

logging.config.dictConfig(LOGGING_DIC)  # 注意：如果不是--logging=None，options.parse_command_line()会覆盖level配置！


# 根据计算机名，选择对应配置
if socket.gethostname().startswith("X"):

    print("X settings")
