#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Zoey Young (ydingmiao@gmail.com)"
import tornado.web
from .base import BaseHandler
import tornado.auth
# from .config import config
import tornado.gen

class AuthLoginHandler(BaseHandler, tornado.auth.GoogleMixin):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        if self.get_current_user():
            self.redirect('/')
        # self.render('login.html', count='-', user=None)
        if self.get_argument("openid.mode", None):
            user = yield self.get_authenticated_user()
            self.set_secure_cookie("auth_user", tornado.escape.json_encode(user))
            self.redirect("/")
            return
        self.authenticate_redirect()

    # @tornado.web.asynchronous
    # def post(self):
    #     if self.get_current_user():
    #         raise tornado.web.HTTPError(403)
    #     email = self.get_argument("email")
    #     password = self.get_argument("password")
    #     if email == config['email'] and password == config['password']:
    #         self.set_secure_cookie('user', config['username'])
    #         self.redirect(self.get_argument('next', '/'))


class AuthLogoutHandler(BaseHandler):
    def get(self):
        self.clear_all_cookies()
        self.redirect("/")
