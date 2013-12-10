#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Zoey Young (ydingmiao@gmail.com)"
from pymongo import MongoClient
COOKIE_SECRET = "/ymPerf5TCOOMRayr7LT8EuXv1PDAk4Ole+VbdxN81A="
DB_NAME = "bc_db"
DB = MongoClient()[DB_NAME]
TITLE = "书签云"
KEYWORDS = "链接,书签,收藏,分享",
DESCRIPTION = "收藏、整理、分享书签，并记录笔记",
PAGE_SIZE = 20
LOG = 'bc_log'
