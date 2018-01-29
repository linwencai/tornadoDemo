# coding:utf8
import json
import logging
import os

from tornado.gen import coroutine
from tornado.httpclient import AsyncHTTPClient, HTTPError
from tornado.web import authenticated

from handler import base


class Editor(base.BaseHandler):
    @authenticated
    def get(self, alert=None):
        path = self.get_argument("path", "")
        fontSize = self.get_argument("fontSize", "16")
        lineHeight = self.get_argument("lineHeight", "22")

        pathList = []
        for dirPath, dirNames, fileNames in os.walk("."):
            for fileName in fileNames:
                # if os.path.splitext(fileName)[1] not in [".py", ".html", ".js", ".css"]:
                if os.path.splitext(fileName)[1] not in (".py", ".html"):
                    continue
                pathList.append(os.path.join(dirPath, fileName)[2:])
        if path and os.path.isfile(path):
            with open(path, "rb") as fp:
                content = fp.read()
        elif path == "stop":
            content = "from tornado.ioloop import IOLoop\nIOLoop.instance().stop()\nresult['msg']='关闭服务器！'"
        # elif path == "reload":
        #     content = "from tornado.autoreload import _reload\n_reload()\nresult['msg']='重启服务器！'"
        else:
            content = ""
        kwargs = locals()
        self.render("editor.html", **kwargs)

    @authenticated
    @coroutine
    def post(self):
        result = {"result": False, "msg": "保存失败"}
        path = self.get_argument("path")
        content = self.get_argument("content")

        if not path or not os.path.isfile(path):
            result["msg"] = u"文件路径不正确：%s" % path
            self.write(result)
            self.finish()
            return

        try:
            fp = open(path, "wb")
            if not content.endswith("\n"):
                content += "\n"
            fp.write(content.encode("utf8"))
            fp.close()

            dirPath, ext = os.path.splitext(path)
            if ext == ".py":
                modulePath = dirPath.replace("\\", ".").replace("/", ".")
                http_client = AsyncHTTPClient()
                response = yield http_client.fetch("http://127.0.0.1:8000/reload/"+modulePath,
                                                   connect_timeout=10, request_timeout=10)
                result = json.loads(response.body.decode())
            else:
                result = {"result": True, "msg": "保存成功"}
        except HTTPError as err:
            logging.warning(u"reload异常:%s" % err)
            result["msg"] = u"reload异常"
        except Exception as err:
            logging.error(u"%s" % err, exc_info=1)
            result["msg"] = u"保存失败：%s" % err

        self.write(result)
        self.finish()


class Runner(base.BaseHandler):
    """执行代码
    """
    log_status = 200

    def run(self):
        code = self.get_argument("code")
        result = {"result": True, "msg": ""}
        logging.info("code:%r" % code)
        try:
            exec(code)
        except SystemExit as err:  # 解决win下reload无法结束进程
            os._exit(err.code)
        except Exception as err:
            logging.exception(err)
            result = {"result": False, "msg": "%s" % err}
        return self.write(result)

    @authenticated
    def get(self, alert=None):
        return self.run()

    @authenticated
    def post(self):
        return self.run()
