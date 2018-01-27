# tornadoDemo

[![Build Status](https://img.shields.io/travis/rust-lang/rust/master.svg)]()
[![Python](https://img.shields.io/badge/Python-2&3-blue.svg)](https://www.python.org/)
[![Tornado](https://img.shields.io/badge/Firefy-1.3-yellowgreen.svg)](https://github.com/tornadoweb/tornado)

tornadoDemo是一个web服务端demo，基于[tornado](https://github.com/tornadoweb/tornado) 框架，异步非阻塞，支持线上编辑代码热更

--------

## 环境
* Python2.7 or Python3
* 生产环境建议使用CentOS Python3 nginx supervisor

## 依赖
* tornado
* psutil
* pycryptodome
* futures
* importlib


## 安装
* 安装Python

  ```
  # CentOS6
  yum install python34 python34-devel -y
  ```
* 安装依赖库

  ```
  python config/get-pip.py
  pip install tornado
  pip install psutil
  pip install pycryptodome

  # 如果是python2
  pip install futures
  pip install importlib
  ```


## 快速开始
1. 运行服务端
  ```
  >>> python main.py
  ```
2. 用浏览器打开http://127.0.0.1:8000

   默认帐号密码都是admin

 :relaxed: