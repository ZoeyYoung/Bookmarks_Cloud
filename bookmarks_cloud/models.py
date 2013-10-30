#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Zoey Young (ydingmiao@gmail.com)"
from .config import *
from .utils import get_bookmark_info
import random
import cgi
import markdown
from bson.objectid import ObjectId


class Page(object):

    def __init__(self, total, cur):
        self.cur = int(cur)
        self.last_page = int((total + PAGE_SIZE - 1) / PAGE_SIZE)
        self.has_next = (self.cur < self.last_page)
        self.has_prev = (self.cur > 1)

from .whoosh_fts import WhooshBookmarks


class User(object):

    def __init__(self, db):
        self.users_collection = db.users

    def insert_or_update(self, new_user):
        user = self.users_collection.find_one(new_user['name'])
        if user:
            pass
        else:
            self.users_collection.insert(new_user)

    def get_user_by_name_and_pwd(self, name, pwd):
        """通过用户名和密码查找用户"""
        return self.users_collection.find_one({'name': name, 'pwd': pwd})


class Bookmark(object):

    def __init__(self, db, user):
        """初始化，包括使用的数据集，全文搜索，和当前用户"""
        self.bookmarks_collection = db.bookmarks
        self.fts = WhooshBookmarks(db)
        self.user = user

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
            {"owner": self.user, "random": {"$gt": r}})
        if not bookmark:
            bookmark = self.bookmarks_collection.find_one(
                {"owner": self.user, "random": {"$lte": r}})
        return bookmark

    def get_count(self):
        """获得当前用户收藏的书签数"""
        return self.bookmarks_collection.find({"owner": self.user}).count()

    def get_by_url(self, url):
        return self.bookmarks_collection.find_one({"owner": self.user, '$or': [
            {"url": url},
            {"url": cgi.escape(url)}
        ]})

    def get_by_tag_page(self, tag, page=1):
        """获得当前用户，特定标签的书签"""
        return self.get_by_owner_tag_page(self.user, tag, page)

    def get_by_owner_tag_page(self, owner, tag, page=1):
        """获得指定用户，特定标签的书签"""
        return self.bookmarks_collection.find({"owner": owner, "tags": tag}).skip((int(page)-1)*PAGE_SIZE).limit(PAGE_SIZE).sort([("post_time", -1)])

    # TODO(Zoey) 这样搜索会比较慢, 需改进
    def get_by_keywords(self, keywords):
        t_keywords = r".*" + keywords + r".*"
        keywords = keywords.split(' ')
        regex_keywords = r".*"
        for key in keywords:
            regex_keywords += key + r".*"
        regex_list = []
        regex_list.append({'title': {'$regex': t_keywords, '$options': '-i'}})
        regex_list.append(
            {'description': {'$regex': t_keywords, '$options': '-i'}})
        regex_list.append({'tags': {'$regex': t_keywords, '$options': '-i'}})
        regex_list.append({'note': {'$regex': t_keywords, '$options': '-i'}})
        regex_list.append(
            {'title': {'$regex': regex_keywords, '$options': '-i'}})
        regex_list.append(
            {'url': {'$regex': regex_keywords, '$options': '-i'}})
        regex_list.append(
            {'description': {'$regex': regex_keywords, '$options': '-i'}})
        regex_list.append(
            {'note': {'$regex': regex_keywords, '$options': '-i'}})
        for key in keywords:
            regex_list.append(
                {'tags': {'$regex': r".*" + key + r".*", '$options': '-i'}})
        return self.bookmarks_collection.find({'$or': regex_list})

    def whoose_ftx(self, keywords, page):
        results = self.fts.search(keywords, int(page))
        search_results = []
        for r in results['results']:
            search_results.append(
                self.bookmarks_collection.find_one(ObjectId(r["nid"])))
        return {'results': search_results, 'total': results['total']}

    def get_all(self):
        return self.bookmarks_collection.find({"owner": self.user}, timeout=False).sort([("post_time", -1)])

    def get_page(self, page):
        """获得当前用户指定页面的书签"""
        return self.bookmarks_collection.find({"owner": self.user}).skip((int(page)-1)*PAGE_SIZE).limit(PAGE_SIZE).sort([("post_time", -1)])

    def get_info(self, url, html=None):
        bookmark = self.get_by_url(url)
        info = get_bookmark_info(url, html)
        if info:
            if bookmark:
                info['note'] = bookmark['note']
                info['tags'] = bookmark['tags']
            else:
                info['note'] = ''
            return info
        else:
            return None

    def insert_or_update(self, new_bookmark):
        bookmark = self.get_by_url(new_bookmark['url'])
        # 更新信息
        # print(info['article'].encode('utf-8'))
        # 如果书签已存在, 则更新信息
        if bookmark:
            if bookmark['title'] is '':
                bookmark['title'] = new_bookmark['title']
            # favicon 如果是从浏览器添加才能更新, 否则通过链接获取
            if new_bookmark['favicon'] != '':
                bookmark['favicon'] = new_bookmark['favicon']
            bookmark['tags'] = new_bookmark['tags']
            bookmark['note'] = new_bookmark['note']
            bookmark['note_html'] = markdown.markdown(
                new_bookmark['note'], extensions=['codehilite(linenums=False)'])
            bookmark['post_time'] = new_bookmark['post_time']
            self.bookmarks_collection.save(bookmark)
            self.fts.update(bookmark)
            return bookmark
        else:
            info = self.get_info(new_bookmark['url'], new_bookmark['html'])
            if info:
                new_bookmark['title'] = info['title']
                new_bookmark['description'] = info['description']
                new_bookmark['article'] = info['article']
                new_bookmark['segmentation'] = info['segmentation']
            new_bookmark['owner'] = self.user
            new_bookmark['note_html'] = markdown.markdown(
                new_bookmark['note'], extensions=['codehilite(linenums=True)'])
            self.bookmarks_collection.insert(new_bookmark)
            self.fts.update(new_bookmark)
            return new_bookmark

    def refresh(self, bookmark, html=None):
        info = self.get_info(bookmark['url'], html)
        if info:
            bookmark['html'] = info['html']
            bookmark['title'] = info['title']
            bookmark['article'] = info['article']
            bookmark['segmentation'] = info['segmentation']
            bookmark['description'] = info['description']
            self.bookmarks_collection.save(bookmark)
            self.fts.update(bookmark)
        return bookmark

    def delete(self, url):
        self.bookmarks_collection.remove({'$or': [
            {"url": url},
            {"url": cgi.escape(url)}
        ]})
        return self.fts.delele_by_url(url)

    def get_random_bookmarks(self):
        random.seed(a=None, version=2)
        r = random.random()
        print(r)
        bookmarks = self.bookmarks_collection.find(
            {"owner": self.user, "random": {"$gt": r}}).limit(PAGE_SIZE)
        if not bookmarks:
            bookmarks = self.bookmarks_collection.find(
                {"owner": self.user, "random": {"$lte": r}}).limit(PAGE_SIZE)
        return bookmarks


class Tags(object):

    def __init__(self, db):
        self.tags = db.tags
