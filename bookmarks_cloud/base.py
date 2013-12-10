#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = "Zoey Young (ydingmiao@gmail.com)"
import tornado.web
from hashlib import md5
from .db import BookmarksDB
from .db import UsersDB
from .db import WebpagesDB
import math

class BaseHandler(tornado.web.RequestHandler):

    @property
    def db(self):
        """使用的数据库"""
        return self.application.db

    @property
    def bm(self):
        return BookmarksDB(self.db, self.current_user)

    @property
    def us(self):
        return UsersDB(self.db)

    @property
    def wp(self):
        return WebpagesDB(self.db)

    @property
    def total(self):
        return self.bm.get_count()

    @property
    def tags(self):
        return self.bm.get_currentuser_tags()

    @property
    def top_tags(self):
        return self.bm.get_tags_by_owner_orderby_count(self.current_user['_id'], 30)

    @property
    def tags_cloud(self):
        """标签云"""
        if self.tags is None or len(self.tags) == 0:
            return []
        max_count = max(tag['count'] for tag in self.tags)
        if max_count < 2:
            max_count = 2
        return [{'tag': tag, 'font_size': round(math.log(tag['count'], max_count), 1)*14 + 8} for tag in self.tags if tag['count'] > 0]

    def avatar(self, size=40):
        if self.current_user:
            return 'http://www.gravatar.com/avatar/' + md5(self.current_user['email'].encode('utf-8').lower()).hexdigest() + '?d=mm&s=' + str(size)

    def get_current_user(self):
        user_json = self.get_secure_cookie("auth_user")
        if not user_json:
            return None
        return tornado.escape.json_decode(user_json)

    def write_error(self, status_code, **kwargs):
        if status_code == 404:
            self.render('404.html')
        if status_code == 500:
            self.render('500.html')
        else:
            super(tornado.web.RequestHandler, self).write_error(status_code, **kwargs)
