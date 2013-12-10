#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Zoey Young (ydingmiao@gmail.com)"
from .config import PAGE_SIZE

class Page(object):

    def __init__(self, total, cur):
        self.cur = int(cur)
        self.last_page = int((total + PAGE_SIZE - 1) / PAGE_SIZE)
        self.has_next = (self.cur < self.last_page)
        self.has_prev = (self.cur > 1)

class Webpage(object):

    def __init__(self):
        self.url = ""
        self.domain = ""
        self.title = ""
        self.favicon = ""
        self.top_image = ""
        self.excerpt = ""
        self.author = ""
        self.content = ""
        self.tags = set()
        self.movies = []
        self.link_hash = ""
        self.raw_html = ""
        self.publish_date = ""
        self.segmentation = ""
