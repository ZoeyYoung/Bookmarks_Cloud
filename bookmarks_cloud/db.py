#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Zoey Young (ydingmiao@gmail.com)"
from .config import *
from .utils import get_webpage_by_readability, get_webpage_by_html, get_webpage_by_goose
import random
import markdown
from bson.objectid import ObjectId
import time
from .utils import format_tags
import urllib.parse
import json
from bson import json_util
from bson.son import SON
from .whoosh_fts import WhooshBookmarks

def json_dumps_docs(cursor):
    return json.dumps(list(cursor), default=json_util.default, sort_keys=True)

def json_dumps_doc(cursor):
    return json.dumps(cursor, default=json_util.default, sort_keys=True)

class UsersDB(object):
    # TODO: 密码应该使用加密策略
    def __init__(self, db):
        self.users_collection = db.users_col

    def insert(self, email, username, pwd):
        """注册新用户"""
        user = self.get_user_by_email({"email": email})
        if user is not None:
            # 邮箱已注册, 判断密码是否正确，若正确，返回用户对象
            if user['pwd'] == pwd:
                return user
            else:
                # 邮箱已注册，但密码不正确，返回空对象
                return None
        else:
            # check weather username is used
            user = self.get_user_by_name(username)
            if user is not None:
                return None
            else:
                # 邮箱未注册，则注册新用户，并返回用户对象
                new_user = {
                    'email': email,
                    'username': username,
                    'pwd': pwd,
                    'follow': []
                }
                oid = self.users_collection.insert(new_user)
                return self.users_collection.find_one(oid)

    def del_pwd(self, user):
        if user is not None:
            del user['pwd']
        return user

    def get_user_by_oid(self, oid):
        return self.del_pwd(self.users_collection.find_one({'_id': oid}))

    def get_user_by_name(self, name):
        return self.del_pwd(self.users_collection.find_one({"name": name}))

    def get_user_by_email(self, email):
        return self.del_pwd(self.users_collection.find_one({"email": email}))

    def get_user_by_name_and_pwd(self, name, pwd):
        """通过用户名和密码查找用户"""
        return self.users_collection.find_one({'name': name, 'pwd': pwd})

    def get_user_by_email_and_pwd(self, email, pwd):
        """通过邮箱和密码查找用户"""
        return self.users_collection.find_one({'email': email, 'pwd': pwd})


class WebpagesDB(object):
    def __init__(self, db):
        self.webpages_collection = db.webpages_col

    def save(self, webpage):
        self.webpages_collection.save(webpage)

    def get_webpage_by_url(self, url):
        """获得Web页面"""
        # url = urllib.parse.unquote(url)
        #　webpage =  self.webpages_collection.find_one({"url": {"$regex": url, "$options": "i"}})
        webpage = self.webpages_collection.find_one({"url": url})
        return webpage

    def get_webpage_by_oid(self, oid):
        """获得Web页面"""
        if not isinstance(oid, ObjectId):
            oid = ObjectId(oid)
        return self.webpages_collection.find_one({"_id": oid})

    def get_webpage_by_readability(self, url, readability=None):
        # 调用工具类的方法，这个方法是网页分析的关键
        webpage = get_webpage_by_readability(url, readability)
        self.save(webpage)
        return webpage

    def get_webpage_by_goose(self, url, html=None):
        # 调用工具类的方法，这个方法是网页分析的关键
        webpage = get_webpage_by_goose(url, html)
        self.save(webpage)
        return webpage

    def get_webpage_by_html(self, url, html=None):
        # 调用工具类的方法，这个方法是网页分析的关键
        webpage = get_webpage_by_html(url, html)
        self.save(webpage)
        return webpage

    def del_webpage_by_url(self, url):
        self.webpages_collection.remove({"url": url})


class BookmarksDB(object):
    """与书签相关的数据库操作
    Attributes:
        bookmarks_collection: 书签在MongoDB中的数据库集
        fts: whoosh全文搜索
        user: 当前用户的用户名
    """
    def __init__(self, db, user):
        """初始化，包括使用的数据集，全文搜索，和当前用户"""
        self.bookmarks_collection = db.bookmarks_col
        self.webpages_db = WebpagesDB(db)
        self.users_db = UsersDB(db)
        self.fts = WhooshBookmarks(db)
        self.user_id = ObjectId(user['_id'])

    # def get_all(self):
    #     """获得当前用户所有书签，一般用分页，这个不会用到"""
    #     return self.bookmarks_collection.find({"owner": self.user_id}, timeout=False).sort([("added_time", -1)])

    def get_users_by_webpage(self, webpage_id):
        """获得收藏了指定页面的用户"""
        if not isinstance(webpage_id, ObjectId):
            webpage_id = ObjectId(webpage_id)
        owners = self.bookmarks_collection.find({"webpage": webpage_id}, ["owner"])
        users = []
        for user in owners:
            user = self.users_db.get_user_by_oid(user["owner"])
            if user is not None:
                users.append(user)
        return users

    def get_recent_bms(self, tag=None, limit=10):
        if tag is None:
            return self.bookmarks_collection.find().limit(int(limit)).sort([("added_time", -1)])
        return self.bookmarks_collection.find({"tags": tag.upper()}).limit(int(limit)).sort([("added_time", -1)])

    def get_bms_by_owner_page(self, owner, page):
        """获得指定用户，指定页面的书签"""
        return self.bookmarks_collection.find({"owner": owner}).skip((int(page)-1)*PAGE_SIZE).limit(PAGE_SIZE).sort([("added_time", -1)])

    def get_bms_by_currentuser_page(self, page):
        """获得当前用户，指定页面的书签"""
        return self.get_bms_by_owner_page(self.user_id, page)

    def get_bms_by_username_page(self, username, page=1):
        """获得指定用户，指定页面的书签"""
        user = self.users_db.get_user_by_name(username)
        return self.get_bms_by_owner_page(user['_id'], page)

    def get_bms_by_tag_page(self, tag, page=1):
        """获取特定标签下的所有书签"""
        return self.bookmarks_collection.find({"tags": tag}).skip((int(page)-1)*PAGE_SIZE).limit(PAGE_SIZE).sort([("added_time", -1)])

    def get_bms_by_owner_tag_page(self, owner, tag, page=1):
        """获得指定用户，特定标签的书签"""
        return self.bookmarks_collection.find({"owner": owner, "tags": tag}).skip((int(page)-1)*PAGE_SIZE).limit(PAGE_SIZE).sort([("added_time", -1)])

    def get_bms_by_currentuser_tag_page(self, tag, page=1):
        """获得当前用户，特定标签的书签"""
        return self.get_bms_by_owner_tag_page(self.user_id, tag, page)

    def get_bms_by_username_tag_page(self, username, tag, page=1):
        """获得指定用户，特定标签的书签"""
        user = self.users_db.get_user_by_name(username)
        return self.get_bms_by_owner_tag_page(user['_id'], tag, page)

    def get_count(self):
        """获得当前用户收藏的书签数"""
        return self.bookmarks_collection.find({"owner": self.user_id}).count()

    def get_tags_by_owner_orderby_count(self, owner, limit=None):
        if not isinstance(owner, ObjectId):
            owner = ObjectId(owner)
        if limit is not None:
            tags = self.bookmarks_collection.aggregate([
                {"$match": {"owner": owner}},
                {"$unwind": "$tags"},
                {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
                {"$sort": SON([("count", -1), ("_id", 1)])},
                {"$limit": int(limit)}
            ])
        else:
            tags = self.bookmarks_collection.aggregate([
                {"$match": {"owner": owner}},
                {"$unwind": "$tags"},
                {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
                {"$sort": SON([("count", -1), ("_id", 1)])}
            ])
        return tags['result']

    def get_tags_by_owner(self, owner):
        tags = self.bookmarks_collection.aggregate([
            {"$match": {"owner": owner}},
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
            {"$sort": SON([("_id", 1)])}
        ])
        return tags['result']

    def get_currentuser_tags(self):
        """获得当前用户所有标签，以及链接数"""
        return self.get_tags_by_owner(self.user_id)

    def get_tags_by_username(self, username, limit=None):
        user = self.users_db.get_user_by_name(username)
        return self.get_tags_by_owner_orderby_count(user['_id'], limit)

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


    def get_bm_by_username_url(self, username, url):
        user = self.users_db.get_user_by_name(username)
        return self.bookmarks_collection.find_one({"owner": user["_id"], "url": url})

    def get_bm_by_url(self, url):
        """获得当前用户，特定URL的书签"""
        return self.bookmarks_collection.find_one({"owner": self.user_id, "url": url})

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
        bookmark = self.get_bm_by_url(url)
        webpage = None
        if bookmark:  # 如果书签存在，则用户已经收藏过，直接获取书签信息
            webpage = self.webpages_db.get_webpage_by_oid(bookmark['webpage'])
            # 这里webpage不应该为空，除非有错误
            if webpage is None:
                webpage = self.webpages_db.get_webpage_by_url(url)
                bookmark['webpage'] = webpage['_id']
                self.save(bookmark, webpage)
        else:  # 否则在webpages中查找是否已解析过该网页
            webpage = self.webpages_db.get_webpage_by_url(url)
        return (bookmark, webpage)

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
            print("old")
            return bookmark
        if webpage:
            new_bookmark['webpage'] = webpage['_id']
            new_bookmark['owner'] = self.user_id
            new_bookmark['title'] = webpage['title']
            new_bookmark['excerpt'] = webpage['excerpt']
            webpage['favicon'] = new_bookmark['favicon']
            new_bookmark['tags'] = format_tags(new_bookmark['tags'])
            new_bookmark['added_time'] = int(time.time())
            new_bookmark['random'] = random.random()
            new_bookmark['is_star'] = 0
            new_bookmark['is_readed'] = 0
            new_bookmark['note_html'] = markdown.markdown(
                new_bookmark['note'], extensions=['codehilite(linenums=True)'])
            self.save(new_bookmark, webpage)
            print("new")
            return new_bookmark

    def save(self, bookmark, webpage=None):
        self.bookmarks_collection.save(bookmark)
        if webpage:
            self.webpages_db.save(webpage)
            # 更新全文搜索索引
            self.fts.update(bookmark, webpage)

    def refresh_by_goose(self, url, html=None):
        webpage = self.webpages_db.get_webpage_by_url(url)
        if html:
            # 调用工具类的方法，这个方法是网页分析的关键
            new_webpage = get_webpage_by_goose(url, html)
            if webpage:
                new_webpage['_id'] = webpage['_id']
                new_webpage['favicon'] = webpage['favicon']
            self.webpages_db.save(new_webpage)
            self.sync_webpage_bookmark(new_webpage)
        return self.get_bookmark_webpage_by_url(url)

    def refresh_by_readability(self, url, readability=None):
        webpage = self.webpages_db.get_webpage_by_url(url)
        if readability:
            # 调用工具类的方法，这个方法是网页分析的关键
            new_webpage = get_webpage_by_readability(url, readability)
            new_webpage['_id'] = webpage['_id']
            new_webpage['favicon'] = webpage['favicon']
            self.webpages_db.save(new_webpage)
            self.sync_webpage_bookmark(new_webpage)
        return self.get_bookmark_webpage_by_url(url)

    def refresh_by_html(self, url, html=None):
        webpage = self.webpages_db.get_webpage_by_url(url)
        if html:
            # 调用工具类的方法，这个方法是网页分析的关键
            new_webpage = get_webpage_by_html(url, html)
            new_webpage['_id'] = webpage['_id']
            new_webpage['favicon'] = webpage['favicon']
            self.webpages_collection.save(new_webpage)
            self.sync_webpage_bookmark(new_webpage)
        return self.get_bookmark_webpage_by_url(url)

    def delete(self, url):
        """删除书签"""
        is_bookmark_deleted = self.bookmarks_collection.remove({"owner": self.user_id, "url": url})
        # 如果该书签已无用户收藏，则删除对应url的webpage
        if self.bookmarks_collection.find({"url": url}).count() == 0:
            self.webpages_db.del_webpage_by_url(url)
        if is_bookmark_deleted['ok'] == 1.0:
            self.fts.delele_by_url(url)
            return True
        return False

    def get_random_bookmarks(self):
        random.seed(a=None, version=2)
        r = random.random()
        bookmarks = self.bookmarks_collection.find(
            {"owner": self.user_id, "random": {"$gt": r}}).limit(PAGE_SIZE)
        if not bookmarks:
            bookmarks = self.bookmarks_collection.find(
                {"owner": self.user_id, "random": {"$lte": r}}).limit(PAGE_SIZE)
        return bookmarks

    def sync_webpage_bookmark(self, webpage):
        bookmarks = self.bookmarks_collection.find({'webpage': webpage['_id']})
        for bookmark in bookmarks:
            bookmark['title'] = webpage['title']
            bookmark['favicon'] = webpage['favicon']
            bookmark['excerpt'] = webpage['excerpt']
            self.bookmarks_collection.save(bookmark)
            # 更新全文搜索索引
            self.fts.update(bookmark, webpage)


class Tags(object):

    def __init__(self, db):
        self.tags = db.tags
