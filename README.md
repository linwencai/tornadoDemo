# tornadoDemo

[![Build Status](https://img.shields.io/travis/rust-lang/rust/master.svg)]()
[![Python](https://img.shields.io/badge/Python-2&3-blue.svg)](https://www.python.org/)
[![Tornado](https://img.shields.io/badge/Firefy-1.3-yellowgreen.svg)](https://github.com/tornadoweb/tornado)

tornadoDemo是一个异步非阻塞的web框架，基于[tornado](https://github.com/tornadoweb/tornado) 框架，封装了定时器、网页代码编辑器、热更

--------

## 环境
* Python2.7 or 3
* 生产环境建议使用CentOS+Python3+nginx+supervisor

## 依赖
* tornado
* psutil
* pycryptodome
* futures[^python2]


[^python2]: python2才需要


## 安装
* 安装Python

  ```
  # CentOS6
  yum install python34 python34-devel -y
  ```
* 安装依赖库

  ```
  pip install tornado
  pip install psutil
  pip install pycryptodome
  pip install futures
  ```


## 快速开始
1. 运行服务端

    ```
    python main.py
    ```

2. 用浏览器打开http://127.0.0.1:8000

   默认帐号密码都是admin

 :relaxed: