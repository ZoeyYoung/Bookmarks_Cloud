#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Zoey Young (ydingmiao@gmail.com)"
import tornado.web
from .base import BaseHandler
import tornado.auth
from tornado import gen

class AuthHandler(BaseHandler, tornado.auth.GoogleMixin):
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
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


class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("auth_user")
        self.redirect(self.get_argument("next", "/"))
