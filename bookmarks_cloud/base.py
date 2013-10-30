#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = "Zoey Young (ydingmiao@gmail.com)"
import tornado.web
from hashlib import md5
from .models import Bookmark
from .models import User
from .utils import get_tags_cloud

class BaseHandler(tornado.web.RequestHandler):

    @property
    def db(self):
        return self.application.db

    @property
    def bm(self):
        return Bookmark(self.db, self.current_user.decode('utf-8'))

    @property
    def us(self):
        return User(self.db)

    @property
    def total(self):
        return self.bm.get_count()

    @property
    def tags(self):
        return self.bm.get_tags()

    @property
    def tags_cloud(self):
        return get_tags_cloud(self.tags)

    def avatar(self, size=40):
        if self.current_user:
            return 'http://www.gravatar.com/avatar/' + md5(self.get_secure_cookie('email').lower()).hexdigest() + '?d=mm&s=' + str(size)

    def get_current_user(self):
        return self.get_secure_cookie("username")
        # user_json = self.get_secure_cookie("auth_user")
        # if not user_json: return None
        # return tornado.escape.json_decode(user_json)

    def write_error(self, status_code, **kwargs):
        if status_code == 404:
            self.render('404.html')
        if status_code == 500:
            self.render('500.html')
        else:
            super(tornado.web.RequestHandler, self).write_error(status_code, **kwargs)
