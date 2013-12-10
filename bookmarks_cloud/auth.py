#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Zoey Young (ydingmiao@gmail.com)"
import tornado.web
import tornado.auth
from .base import BaseHandler

class SignInHandler(BaseHandler):
    """登录"""
    def get(self):
        self.render('auth.html')

    @tornado.web.asynchronous
    def post(self):
        # 是否重复登录
        if self.get_current_user():
            self.redirect(self.get_argument('next', '/'), permanent=True)
            raise tornado.web.HTTPError(403)
        email = self.get_argument("email")
        password = self.get_argument("password")
        user = self.us.get_user_by_email_and_pwd(email, password)
        if user:
            user['_id'] = str(user['_id'])
            if 'follow' in user:
                del user['follow']
            self.set_secure_cookie('auth_user', tornado.escape.json_encode(user))
            self.redirect(self.get_argument('next', '/'), permanent=True)
        else:
            # 登录不成功前台应该有提示
            print("登录失败")


class SignUpHandler(BaseHandler):

    def get(self):
        self.render('auth.html')

    """注册"""
    @tornado.web.asynchronous
    def post(self):
        # 是否重复登录
        if self.get_current_user():
            self.redirect(self.get_argument('next', '/'), permanent=True)
            raise tornado.web.HTTPError(403)
        email = self.get_argument("email")
        username = self.get_argument("username")
        password = self.get_argument("password")
        user = self.us.insert(email, username, password)
        if user:
            user['_id'] = str(user['_id'])
            self.set_secure_cookie('auth_user', tornado.escape.json_encode(user))
            self.redirect(self.get_argument('next', '/'), permanent=True)
        else:
            # 注册不成功前台应该有提示
            print("注册失败")


class LogoutHandler(BaseHandler):

    def get(self):
        self.clear_cookie("auth_user")
        self.redirect(self.get_argument("next", "/"))
