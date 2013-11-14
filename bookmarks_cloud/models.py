#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Zoey Young (ydingmiao@gmail.com)"
from .config import *
from .utils import get_webpage_by_readability, get_webpage_by_html
import random
import markdown
from bson.objectid import ObjectId
import time
from .utils import format_tags

class Page(object):

    def __init__(self, total, cur):
        self.cur = int(cur)
        self.last_page = int((total + PAGE_SIZE - 1) / PAGE_SIZE)
        self.has_next = (self.cur < self.last_page)
        self.has_prev = (self.cur > 1)

from .whoosh_fts import WhooshBookmarks


class User(object):
    # TODO: 密码应该使用加密策略
    def __init__(self, db):
        self.users_collection = db.users

    def insert(self, email, pwd):
        """注册新用户"""
        user = self.users_collection.find_one(email)
        if user:
            # 邮箱已注册, 判断密码是否正确，若正确，返回用户对象
            if user['pwd'] == pwd:
                return user
            else:
                # 邮箱已注册，但密码不正确，返回空对象
                return None
        else:
            # 邮箱未注册，则注册新用户，并返回用户对象
            new_user = {
                'email': email,
                'pwd': pwd
            }
            user = self.users_collection.insert(new_user)
            return user

    def get_user_by_name_and_pwd(self, name, pwd):
        """通过用户名和密码查找用户"""
        return self.users_collection.find_one({'name': name, 'pwd': pwd})

    def get_user_by_email_and_pwd(self, email, pwd):
        """通过邮箱和密码查找用户"""
        return self.users_collection.find_one({'email': email, 'pwd': pwd})


class Bookmark(object):
    """与书签相关的数据库操作
    Attributes:
        bookmarks_collection: 书签在MongoDB中的数据库集
        fts: whoosh全文搜索
        user: 当前用户的用户名
    """
    def __init__(self, db, user):
        """初始化，包括使用的数据集，全文搜索，和当前用户"""
        self.bookmarks_collection = db.bookmarks_col
        self.webpages_collection = db.webpages_col
        self.fts = WhooshBookmarks(db)
        self.user_id = ObjectId(user['_id'])

    def get_all(self):
        """获得当前用户所有书签，一般用分页，这个不会用到"""
        return self.bookmarks_collection.find({"owner": self.user_id}, timeout=False).sort([("added_time", -1)])

    def get_by_page(self, page):
        """获得当前用户，指定页面的书签"""
        return self.get_by_owner_page(self.user_id, page)

    def get_by_owner_page(self, owner, page):
        """获得指定用户，指定页面的书签"""
        return self.bookmarks_collection.find({"owner": owner}).skip((int(page)-1)*PAGE_SIZE).limit(PAGE_SIZE).sort([("added_time", -1)])

    def get_by_tag_page(self, tag, page=1):
        """获得当前用户，特定标签的书签"""
        return self.get_by_owner_tag_page(self.user_id, tag, page)

    def get_by_owner_tag_page(self, owner, tag, page=1):
        """获得指定用户，特定标签的书签"""
        return self.bookmarks_collection.find({"owner": owner, "tags": tag}).skip((int(page)-1)*PAGE_SIZE).limit(PAGE_SIZE).sort([("added_time", -1)])

    def get_count(self):
        """获得当前用户收藏的书签数"""
        return self.bookmarks_collection.find({"owner": self.user_id}).count()

    def get_tags(self):
        """获得所有标签，以及链接数"""
        from bson.son import SON
        tags = self.bookmarks_collection.aggregate([
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
            {"$sort": SON([("_id", 1), ("count", -1)])}
        ])
        return tags['result']

    def get_random_one(self):
        """随机获取当前用户的一个书签"""
        random.seed(a=None, version=2)
        r = random.random()
        bookmark = self.bookmarks_collection.find_one(
            {"owner": self.user_id, "random": {"$gt": r}})
        if not bookmark:
            bookmark = self.bookmarks_collection.find_one(
                {"owner": self.user_id, "random": {"$lte": r}})
        return bookmark

    def get_by_url(self, url):
        """获得当前用户，特定URL的书签"""
        return self.bookmarks_collection.find_one({"owner": self.user_id, "url": url})

    def get_webpage_by_url(self, url):
        """获得Web页面"""
        return self.webpages_collection.find_one({"url": url})

    def get_webpage_by_oid(self, oid):
        """获得Web页面"""
        return self.webpages_collection.find_one({"_id": oid})

    def whoose_ftx(self, keywords, page):
        """全文搜索"""
        results = self.fts.search(keywords, int(page))
        search_results = []
        for r in results['results']:
            search_results.append(
                self.bookmarks_collection.find_one(ObjectId(r["nid"])))
        return {'results': search_results, 'total': results['total']}


    def get_bookmark_webpage_by_url(self, url):
        """获取当前用户，指定URL书签的信息"""
        # 用户是否已经收藏该书签
        bookmark = self.get_by_url(url)
        webpage = None
        if bookmark:  # 如果书签存在，则用户已经收藏过，直接获取书签信息
            webpage = self.get_webpage_by_oid(bookmark['webpage'])
        else:  # 否则在webpages中查找是否已解析过该网页
            webpage = self.get_webpage_by_url(url)
        return (bookmark, webpage)


    def get_webpage_by_readability(self, url, readability=None):
        # 调用工具类的方法，这个方法是网页分析的关键
        webpage = get_webpage_by_readability(url, readability)
        self.webpages_collection.save(webpage)
        return webpage


    def get_webpage_by_html(self, url, html=None):
        # 调用工具类的方法，这个方法是网页分析的关键
        webpage = get_webpage_by_html(url, html)
        self.webpages_collection.save(webpage)
        return webpage

    def insert_or_update(self, new_bookmark):
        # 是否已收藏过该书签
        (bookmark, webpage) = self.get_bookmark_webpage_by_url(new_bookmark['url'])
        # 如果书签已存在, 则更新信息
        if bookmark:
            # favicon 如果是从浏览器添加才能更新, 否则通过链接获取
            if new_bookmark['favicon'] != '':
                bookmark['favicon'] = new_bookmark['favicon']
                webpage['favicon'] = new_bookmark['favicon']
            bookmark['tags'] = format_tags(new_bookmark['tags'])
            bookmark['note'] = new_bookmark['note']
            bookmark['note_html'] = markdown.markdown(
                new_bookmark['note'], extensions=['codehilite(linenums=False)'])
            bookmark['added_time'] = int(time.time())
            self.save(bookmark, webpage)
            return bookmark
        else:
            new_bookmark['webpage'] = webpage['_id']
            new_bookmark['owner'] = self.user_id
            new_bookmark['title'] = webpage['title']
            new_bookmark['excerpt'] = webpage['excerpt']
            webpage['favicon'] = new_bookmark['favicon']
            new_bookmark['lead_image_url'] = webpage['lead_image_url']
            new_bookmark['tags'] = format_tags(new_bookmark['tags'])
            new_bookmark['added_time'] = int(time.time())
            new_bookmark['random'] = random.random()
            new_bookmark['is_star'] = 0
            new_bookmark['is_readed'] = 0
            new_bookmark['note_html'] = markdown.markdown(
                new_bookmark['note'], extensions=['codehilite(linenums=True)'])
            self.save(new_bookmark, webpage)
            return new_bookmark

    def save(self, bookmark, webpage=None):
        self.bookmarks_collection.save(bookmark)
        if webpage:
            self.webpages_collection.save(webpage)
            # 更新全文搜索索引
            self.fts.update(bookmark, webpage)

    def refresh_by_readability(self, url, readability=None):
        (bookmark, webpage) = self.get_bookmark_webpage_by_url(url)
        if readability:
            # 调用工具类的方法，这个方法是网页分析的关键
            new_webpage = get_webpage_by_readability(url, readability)
            new_webpage['_id'] = webpage['_id']
            new_webpage['favicon'] = webpage['favicon']
            self.sync_webpage_bookmark(new_webpage, bookmark)
            self.save(bookmark, new_webpage)
        return (bookmark, new_webpage)

    def refresh_by_html(self, url, html=None):
        (bookmark, webpage) = self.get_bookmark_webpage_by_url(url)
        if html:
        # 调用工具类的方法，这个方法是网页分析的关键
            new_webpage = get_webpage_by_html(url, html)
            new_webpage['_id'] = webpage['_id']
            new_webpage['favicon'] = webpage['favicon']
            self.sync_webpage_bookmark(new_webpage, bookmark)
            self.save(bookmark, new_webpage)
        return (bookmark, new_webpage)

    def delete(self, url):
        """删除书签"""
        return self.bookmarks_collection.remove({"owner": self.user_id, "url": url})

    def get_random_bookmarks(self):
        random.seed(a=None, version=2)
        r = random.random()
        bookmarks = self.bookmarks_collection.find(
            {"owner": self.user_id, "random": {"$gt": r}}).limit(PAGE_SIZE)
        if not bookmarks:
            bookmarks = self.bookmarks_collection.find(
                {"owner": self.user_id, "random": {"$lte": r}}).limit(PAGE_SIZE)
        return bookmarks


    def sync_webpage_bookmark(self, webpage, bookmark):
        bookmark['title'] = webpage['title']
        bookmark['excerpt'] = webpage['excerpt']
        bookmark['lead_image_url'] = webpage['lead_image_url']


class Tags(object):

    def __init__(self, db):
        self.tags = db.tags
