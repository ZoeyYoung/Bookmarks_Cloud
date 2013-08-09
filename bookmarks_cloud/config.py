#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Zoey Young (ydingmiao@gmail.com)"
import pymongo
config = {
    "cookie_secret": "/ymPerf5TCOOMRayr7LT8EuXv1PDAk4Ole+VbdxN81A=",
    "username": "your_name",
    "email": "ydingmiao@gmail.com",
    "password": 'your_password',
    "db": pymongo.MongoClient().bookmarks_cloud,
    "title": "书签云",
    "url": "",
    "keywords": "链接,书签,收藏,分享",
    "description": "收藏、整理、分享书签，并记录笔记",
    "analytics": '''<script type="text/javascript">
                    </script>
                  ''',
    "page_size": 20
}
