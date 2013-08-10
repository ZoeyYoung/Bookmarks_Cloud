#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Zoey Young (ydingmiao@gmail.com)"
import tornado.web
import tornado.template
from .base import BaseHandler
import json
import time
import random
from .utils import fetch_url
from .utils import get_keywords
from .utils import format_tags
from .models import Page
from tornado import gen

class BookmarkModule(tornado.web.UIModule):

    def render(self, bookmark):
        try:
            return self.render_string('modules/bookmark.html', bookmark=bookmark)
        except KeyError:
            print('KeyError ->', bookmark)


class PagerModule(tornado.web.UIModule):

    def render(self, page):
        try:
            return self.render_string('modules/pager.html', page=page)
        except KeyError:
            print('KeyError ->', page)


class IndexHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self, page=1):
        bookmarks = self.bm.get_page(int(page))
        page = Page(self.total, page)
        self.render('index.html', bookmarks=bookmarks, page=page)


class AjaxBookmarkHandler(BaseHandler):

    @tornado.web.authenticated
    def post(self):
        page = self.get_argument('page')
        tag = self.get_argument('tag')
        keywords = self.get_argument('keywords')
        if tag:
            bookmarks = self.bm.get_by_tag(tag, int(page))
            page = Page(bookmarks.count(), int(page))
        elif keywords:
            results = self.bm.whoose_ftx(keywords, int(page))
            bookmarks = results['results']
            page = Page(results['total'], int(page))
        else:
            bookmarks = self.bm.get_page(int(page))
            page = Page(bookmarks.count(), int(page))
        self.render('list.html', bookmarks=bookmarks, page=page)


class BookmarkGetInfoHandler(BaseHandler):

    @tornado.web.authenticated
    @gen.coroutine
    def get(self, *args):
        url = self.get_argument('url')
        response = yield fetch_url(url)
        print(fetch_url.cache_info())
        if response:
            info = self.bm.get_info(url, html=response.body)
            if info:
                self.write(json.dumps({
                    'success': 'true',
                    'favicon': info['favicon'],
                    'title': info['title'],
                    'description': info['description'],
                    'tags': info['tags'],
                    'note': info['note']
                }))
        else:
            self.write(json.dumps({'success': 'false'}))


class BookmarkGetDetailHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self, *args):
        url = self.get_argument('url')
        bookmark = self.bm.get_by_url(url)
        suggest_tags = get_keywords(bookmark['article'])
        if bookmark:
            self.write(json.dumps({
                'success': 'true',
                'title': bookmark['title'],
                'favicon': bookmark['favicon'],
                'description': bookmark['description'],
                'tags': ','.join(bookmark['tags']),
                'note': bookmark['note'],
                'article': bookmark['article'],
                'suggest_tags': suggest_tags
            }))
        else:
            self.write(json.dumps({'success': 'false'}))


class BookmarkRefreshHandler(BaseHandler):

    @tornado.web.authenticated
    @gen.coroutine
    def get(self, *args):
        url = self.get_argument('url')
        bookmark = self.bm.get_by_url(url)
        if bookmark:
            response = yield fetch_url(url)
            if response:
                bookmark = self.bm.refresh(bookmark, html=response.body)
                bookmark_module = tornado.escape.to_basestring(
                    self.render_string('modules/bookmark.html', bookmark=bookmark))
                self.write(json.dumps({
                    'success': 'true',
                    'bookmark_module': bookmark_module,
                    'title': bookmark['title'],
                    'article': tornado.escape.to_basestring(bookmark['article'])
                }))
            else:
                self.write(json.dumps({'success': 'false'}))
        else:
            self.write(json.dumps({'success': 'false'}))


class BookmarkGetArticleHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self, *args):
        url = self.get_argument('url')
        bookmark = self.bm.get_by_url(url)
        if bookmark:
            if bookmark['article'] == '':
                bookmark = self.bm.refresh(bookmark)
            self.write(json.dumps({
                'success': 'true',
                'title': bookmark['title'],
                'article': bookmark['article']
            }))
        else:
            self.write(json.dumps({'success': 'false'}))


class BookmarkAddHandler(BaseHandler):

    @tornado.web.authenticated
    def post(self, *args):
        note = self.get_argument('note')
        post_time = int(time.time())
        bookmark = dict(
            url=self.get_argument('url'),
            title=self.get_argument('title'),
            favicon=self.get_argument('favicon'),
            tags=format_tags(self.get_argument('tags')),
            note=note,
            post_time=post_time,
            random=random.random(),
            html=self.get_argument('html')
        )
        bookmark = self.bm.insert_or_update(bookmark)
        bookmark_module = tornado.escape.to_basestring(
            self.render_string('modules/bookmark.html', bookmark=bookmark))
        self.write(json.dumps({
            'success': 'true',
            'bookmark_module': bookmark_module,
            'article': tornado.escape.to_basestring(bookmark['article'])
        }))


class BookmarkDelHandler(BaseHandler):

    @tornado.web.authenticated
    def post(self, *args):
        url = self.get_argument('url')
        if self.bm.delete(url) == 1:
            self.write(json.dumps({'success': 'true'}))
        else:
            self.write(json.dumps({'success': 'false'}))


class TagBookmarksHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self, page, tag):
        bookmarks = self.bm.get_by_tag(tag, int(page))
        page = Page(bookmarks.count(), int(page))
        self.render('tags_bookmarks.html', bookmarks=bookmarks, page=page, cur_tag=tag, tag_count=bookmarks.count())


class TagsCloudHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        self.render('tags_cloud.html', tags_cloud=self.tags_cloud)


class RandomBookmarksHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        bookmarks = self.bm.get_random_bookmarks()
        self.render('random_bookmarks.html', bookmarks=bookmarks)


class RandomBookmarkHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        bookmark = self.bm.get_random_one()
        bookmark_module = tornado.escape.to_basestring(
            self.render_string('modules/bookmark.html', bookmark=bookmark))
        self.write(json.dumps({
            'success': 'true',
            'url': bookmark['url'],
            'title': bookmark['title'],
            'article': bookmark['article'],
            'bookmark_module': bookmark_module
        }))


# class SearchHandler(BaseHandler):
#     """搜索书签
#     """
#     @tornado.web.authenticated
#     def get(self):
#         tags = Bookmark.get_tags()
#         tags_cloud = get_tags_cloud(tags)
#         keywords = self.get_argument('keywords')
#         result = Bookmark.get_by_keywords(keywords)
#         count = result.count()
#         self.render('search_result.html', keywords=keywords, tags_cloud=tags_cloud, bookmarks=result, count=count)


class FullTextSearchHandler(BaseHandler):
    """搜索书签
    """
    @tornado.web.authenticated
    def get(self):
        keywords = self.get_argument('keywords')
        results = self.bm.whoose_ftx(keywords, 1)
        page = Page(results['total'], 1)
        self.render('search_result.html', keywords=keywords, bookmarks=results['results'], count=results['total'], page=page)


class TagsHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        tagsstr = ','.join([tag['_id'] for tag in self.tags])
        self.write(json.dumps({
            'tags': tagsstr
        }))


class SegmentationHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self, url):
        bookmark = self.bm.get_by_url(url)
        self.render('segmentation.html', bookmark=bookmark)
