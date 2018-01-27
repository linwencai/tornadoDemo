# coding:utf8
# 测试
import time
import tornado.gen
import tornado.ioloop
from tornado.web import RequestHandler
from tornado.httpclient import AsyncHTTPClient


class Sleep(RequestHandler):
    @tornado.gen.coroutine
    def get(self, *args):
        second = float(args[0]) if args else 1
        yield tornado.gen.sleep(second)
        result = "get args:%s<br/>ip:%s<br/>time:%d<br/>second:%s" % (
                self.request.arguments, self.request.remote_ip, time.time(), second)
        self.write(result)

    @tornado.gen.coroutine
    def post(self, *args):
        second = float(args[0]) if args else 1
        yield tornado.gen.Task(tornado.ioloop.IOLoop.instance().add_timeout,
                               time.time() + (float(args[0]) if args else 1))
        result = "post args:%s<br/>ip:%s<br/>time:%d<br/>second:%s" % (
            self.request.arguments, self.request.remote_ip, time.time(), second)
        self.write(result)


class Test(RequestHandler):
    url = "http://127.0.0.1:8000/sleep/3"

    @tornado.gen.coroutine
    def get(self):
        print("1%s" % time.time())
        http_client = AsyncHTTPClient()
        response = yield http_client.fetch(self.url, method="POST", body="a=123")
        result = response.body if isinstance(response.body, str) else response.body.decode()
        print("2%s" % time.time())
        self.write("result:%s" % result)

    # @tornado.web.asynchronous
    # def get(self):
    #     print("1", time.time())
    #     http_client = AsyncHTTPClient()
    #     http_client.fetch(self.url, self._end, method="POST", body="a=123")
    #
    # def _end(self, response):
    #     result = response.body if isinstance(response.body, str) else response.body.decode()
    #     print("2", time.time())
    #     self.write("result:%s" % result)
    #     self.finish()


class Redirect(RequestHandler):
    def get(self):
        self.redirect("/redirect")


# ab -n 10000 -c 500 "http://127.0.0.1:8001/stress"
class Stress(RequestHandler):
    def get(self):
        self.write("ok")

    def post(self):
        self.write("ok")

# 测试 end
