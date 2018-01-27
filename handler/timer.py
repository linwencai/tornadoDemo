# coding:utf8
from tornado.web import authenticated

from handler import base
from manager.timerMgr import timerDict


class ListHandler(base.BaseHandler):
    @authenticated
    def get(self, alert=None):
        paginate = int(self.get_argument("paginate", self.paginate))
        page = int(self.get_argument("page", 1))
        count = len(timerDict)
        maxPage = (count + paginate - 1) // paginate
        minRange = max(1, min(page-5, maxPage-9))
        maxRange = min(maxPage, minRange+9)
        timerList = list(timerDict.values())[(page-1)*paginate:page*paginate]

        kwargs = locals()
        self.render("timer.html", **kwargs)

    @authenticated
    def post(self):
        action = self.get_argument("action")
        # timerName = self.get_argument("timerName")
        # timer = timerDict.get(timerName)

        timerId = int(self.get_argument("timerId"))
        timer = timerDict.getById(timerId)

        if not timer:
            alert = [u"warning", u"未找到定时器:%s" % timerId]
        elif action == "start":
            timer.start()
            alert = [u"success", u"启动成功"]
        elif action == "stop":
            timer.stop()
            alert = [u"success", u"停止成功"]
        elif action == "run":
            timer.run(True)
            alert = [u"success", u"运行成功"]
        else:
            alert = [u"warning", u"无效操作:%s" % action]
        return self.get(alert)
