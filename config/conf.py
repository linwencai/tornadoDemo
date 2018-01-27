# coding:utf8
from __future__ import unicode_literals
import os
import socket
# import sys

logLevel = "INFO"  # 日志等级 NOTSET|DEBUG|INFO|WARNING|ERROR

process = False  # 多进程模式 {True:根据cpu核心数，数字:子进程数，False：单进程}
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


# db_settings = {
#     'database': 'peewee',
#     'host': 'localhost',
#     'user': 'root',
#     'password': 'root',
#     'port': 3306,
#     'charset': 'utf8'
# }


# 根据计算机名，选择对应配置
if socket.gethostname().startswith("X"):

    print("X settings")
