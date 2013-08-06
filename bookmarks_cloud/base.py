#!/usr/bin/python
# -*- coding: utf-8 -*-

import tornado.web
from .config import config
from hashlib import md5
from .models import Bookmark


class BaseHandler(tornado.web.RequestHandler):

    @property
    def db(self):
        return self.settings.db

    @property
    def total(self):
        return Bookmark.get_count()

    def avatar(self, size=40):
        return 'http://www.gravatar.com/avatar/' + md5(config['email'].lower().encode('utf-8')).hexdigest() + '?d=mm&s=' + str(size)

    def get_current_user(self):
        return self.get_secure_cookie("user")

    def write_error(self, status_code, **kwargs):
        if status_code == 404:
            self.render('404.html')
        if status_code == 500:
            self.render('500.html')
        else:
            super(tornado.web.RequestHandler, self).write_error(status_code, **kwargs)
