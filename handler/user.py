# coding:utf8
import logging

from handler import base


class LoginHandler(base.BaseHandler):
    def get(self, alert=None):
        self.render("login.html", alert=alert)

    def post(self):
        username = self.get_argument("username")
        password = self.get_argument("password")
        remember = self.get_argument("remember", False)
        email = self.get_argument("email", "")
        ip = self.request.headers.get("X-Real-IP", self.request.remote_ip)

        logging.info("login username:%s password:%s ip:%s" % (username, password, ip))

        if username.lower() != "admin" or password != "admin":
            return self.get(["warning", "账号或密码错误"])

        remember = 1 if remember else None
        self.set_secure_cookie("username", username, expires_days=remember)
        self.set_secure_cookie("email", email, expires_days=remember)
        self.set_secure_cookie("ip", ip, expires_days=remember)
        self.redirect("/")
        return


class LogoutHandler(base.BaseHandler):
    def get(self):
        self.clear_cookie("username")
        self.redirect("/")


