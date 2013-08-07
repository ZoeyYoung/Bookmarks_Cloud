#!/usr/bin/python
# -*- coding: utf-8 -*-
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
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_user": "your_email@gmail.com",
    "smtp_password": "",
    "page_size": 20
}
