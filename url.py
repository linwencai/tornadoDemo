# coding:utf8
import logging


def urls(ReloadHandler):
    url = [(r"/reload/([\w\.]+)", ReloadHandler)]
    try:
        from handler import editor
        url.extend([(r"/editor", editor.Editor),
                    (r"/runner", editor.Runner),
                    ])

        from handler import log
        url.extend([(r"/log", log.LogHandler),
                    (r"/log/ws", log.WSHandler),
                    (r"/log/status", log.StatusHandler),
                    ])

        from handler import index, user, timer, test
        url.extend([(r"/", index.IndexHandler),
                    (r"/ws", index.WSHandler),
                    (r"/login", user.LoginHandler),
                    (r"/logout", user.LogoutHandler),
                    # (r"/echarts", echarts.EchartsHandler),
                    (r"/timer", timer.ListHandler),
                    (r"/timer/(\w+)/(\d+)", timer.ListHandler),

                    (r"/sleep/(\d+\.\d+|\d*)", test.Sleep),
                    (r"/test", test.Test),
                    (r"/stress", test.Stress),
                    (r"/redirect", test.Redirect),
                    # (r"/(apple-touch-icon\.png)", tornado.web.StaticFileHandler, dict(path=settings['static_path'])),

                    (r"/.*", test.Test),  # 测试，匹配任意地址，要放最后！
                    ])
    except Exception as err:
        logging.exception("handler err:%s" % err)
    return url
