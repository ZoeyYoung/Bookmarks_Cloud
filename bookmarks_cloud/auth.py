#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Zoey Young (ydingmiao@gmail.com)"
import tornado.web
import tornado.auth
from .base import BaseHandler

class AuthHandler(BaseHandler):

    def get(self):
        self.render('login.html')

    @tornado.web.asynchronous
    def post(self):
        if self.get_current_user():
            raise tornado.web.HTTPError(403)
        name = self.get_argument("name")
        password = self.get_argument("password")
        user = self.us.get_user_by_name_and_pwd(name, password)
        if user:
            self.set_secure_cookie('username', user['name'])
            self.set_secure_cookie('email', user['email'])
            self.redirect(self.get_argument('next', '/'))


class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("auth_user")
        self.redirect(self.get_argument("next", "/"))
