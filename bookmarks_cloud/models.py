#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .config import config
from .utils import get_bookmark_info
import random
import cgi
import markdown

page_size = config['page_size']


# Bookmark = namedtuple('Bookmark', ['_id', 'article', 'description', 'favicon', 'note', 'note_html', 'post_time', 'tags', 'title', 'url'])


class Page(object):

    def __init__(self, total, cur):
        self.cur = int(cur)
        self.last_page = int((total+page_size-1)/page_size)
        self.has_next = (self.cur < self.last_page)
        self.has_prev = (self.cur > 1)

bookmarks_collection = config['db'].bookmarks


class Bookmark(object):

    def __init__(self):
        pass

    # 获得所有标签，以及链接数
    @staticmethod
    def get_tags():
        from bson.son import SON
        tags = bookmarks_collection.aggregate([
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
            {"$sort": SON([("_id", 1), ("count", -1)])}
        ])
        return tags['result']

    @staticmethod
    def get_random_one():
        random.seed(a=None, version=2)
        r = random.random()
        bookmark = bookmarks_collection.find_one({"random": {"$gt": r}})
        if not bookmark:
            bookmark = bookmarks_collection.find_one({"random": {"$lte": r}})
        return bookmark

    @staticmethod
    def get_count():
        return bookmarks_collection.count()

    @staticmethod
    def get_by_url(url):
        return bookmarks_collection.find_one({'$or': [
            {"url": url},
            {"url": cgi.escape(url)}
        ]})

    @staticmethod
    def get_by_tag(tag, page):
        return bookmarks_collection.find({"tags": tag}).skip((page-1)*page_size).limit(page_size).sort([("post_time", -1)])

    # TODO(Zoey) 这样搜索会比较慢, 需改进
    @staticmethod
    def get_by_keywords(keywords):
        t_keywords = r".*" + keywords + r".*"
        keywords = keywords.split(' ')
        regex_keywords = r".*"
        for key in keywords:
            regex_keywords += key + r".*"
        regex_list = []
        regex_list.append({'title': {'$regex': t_keywords, '$options': '-i'}})
        regex_list.append({'description': {'$regex': t_keywords, '$options': '-i'}})
        regex_list.append({'tags': {'$regex': t_keywords, '$options': '-i'}})
        regex_list.append({'note': {'$regex': t_keywords, '$options': '-i'}})
        regex_list.append({'title': {'$regex': regex_keywords, '$options': '-i'}})
        regex_list.append({'url': {'$regex': regex_keywords, '$options': '-i'}})
        regex_list.append({'description': {'$regex': regex_keywords, '$options': '-i'}})
        regex_list.append({'note': {'$regex': regex_keywords, '$options': '-i'}})
        for key in keywords:
            regex_list.append({'tags': {'$regex': r".*"+key+r".*", '$options': '-i'}})
        return bookmarks_collection.find({'$or': regex_list})

    @staticmethod
    def get_all():
        return bookmarks_collection.find(timeout=False).sort([("post_time", -1)])

    @staticmethod
    def get_page(page):
        return bookmarks_collection.find().skip((page-1)*page_size).limit(page_size).sort([("post_time", -1)])

    @staticmethod
    def get_info(url, html=''):
        bookmark = Bookmark.get_by_url(url)
        info = get_bookmark_info(url, html)
        if info:
            if bookmark:
                info['note'] = bookmark['note']
                info['tags'] = bookmark['tags']
                # info['is_star'] = bookmark['is_star']
                # info['is_readed'] = bookmark['is_readed']
            else:
                info['note'] = ''
                # info['is_star'] = 0
                # info['is_readed'] = 0
            return info
        else:
            return None

    @staticmethod
    def insert_or_update(new_bookmark):
        bookmark = Bookmark.get_by_url(new_bookmark['url'])
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
            bookmark['note_html'] = markdown.markdown(new_bookmark['note'], extensions=['codehilite(linenums=False)'])
            bookmark['post_time'] = new_bookmark['post_time']
            bookmarks_collection.save(bookmark)
            return bookmark
        else:
            info = Bookmark.get_info(new_bookmark['url'], new_bookmark['html'])
            if info:
                if not info['title'] is '':
                    new_bookmark['title'] = info['title']
                new_bookmark['description'] = info['description']
                new_bookmark['article'] = info['article']
            new_bookmark['note_html'] = markdown.markdown(new_bookmark['note'], extensions=['codehilite(linenums=True)'])
            bookmarks_collection.insert(new_bookmark)
            return new_bookmark

    @staticmethod
    def refresh(bookmark):
        info = Bookmark.get_info(bookmark['url'])
        if info:
            bookmark['title'] = info['title']
            bookmark['article'] = info['article']
            bookmark['segmentation'] = info['segmentation']
            bookmark['description'] = info['description']
            bookmarks_collection.save(bookmark)
        return bookmark

    @staticmethod
    def delete(url):
        bookmarks_collection.remove({'$or': [
            {"url": url},
            {"url": cgi.escape(url)}
        ]})

    @staticmethod
    def get_random_bookmarks():
        random.seed(a=None, version=2)
        r = random.random()
        print(r)
        bookmarks = bookmarks_collection.find({"random": {"$gt": r}}).limit(page_size)
        if not bookmarks:
            bookmarks = bookmarks_collection.find({"random": {"$lte": r}}).limit(page_size)
        return bookmarks
