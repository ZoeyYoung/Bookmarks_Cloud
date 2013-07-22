#!/usr/bin/env python
# -*- coding: utf-8 -*-
import tornado.web
from .base import BaseHandler
import json
import tornado.auth
from .config import config
import logging


class AuthLoginHandler(BaseHandler):
    def get(self):
        if self.get_current_user():
            self.redirect('/')
        self.render('login.html', count='-', user=None)

    @tornado.web.asynchronous
    def post(self):
        if self.get_current_user():
            raise tornado.web.HTTPError(403)
        email = self.get_argument("email")
        password = self.get_argument("password")
        if email == config['email'] and password == config['password']:
            self.set_secure_cookie('user', config['username'])
            self.redirect(self.get_argument('next', '/'))


class AuthLogoutHandler(BaseHandler):
    def get(self):
        self.clear_all_cookies()
        self.redirect(self.get_argument("next", "/"))
