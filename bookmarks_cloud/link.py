#!/usr/bin/env python
# -*- coding: utf-8 -*-
import tornado.web
import tornado.template
from .base import BaseHandler
import json
import time
import random
from .utils import format_tags
from .utils import get_tags_cloud
from .models import Page, Link


class LinkModule(tornado.web.UIModule):

    def render(self, link):
        try:
            return self.render_string('modules/link.html', link=link)
        except KeyError:
            print('KeyError ->', link)


class PagerModule(tornado.web.UIModule):

    def render(self, page):
        try:
            return self.render_string('modules/pager.html', page=page)
        except KeyError:
            print('KeyError ->', page)


class IndexHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self, page=1):
        links = Link.get_page(page)
        page = Page(Link.get_count(), page)
        tags = Link.get_tags()
        tags_cloud = get_tags_cloud(tags)
        self.render('index.html', tags_cloud=tags_cloud,
                    links=links, count=Link.get_count(), page=page)


class LinkHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self, page):
        tags = Link.get_tags()
        links = Link.get_page(int(page))
        page = Page(Link.get_count(), int(page))
        tags_cloud = get_tags_cloud(tags)
        self.render('index.html', tags_cloud=tags_cloud,
                    links=links, count=Link.get_count(), page=page)


class AjaxLinkHandler(BaseHandler):

    def post(self):
        page = self.get_argument('page')
        tag = self.get_argument('tag')
        if tag is '':
            links = Link.get_page(int(page))
        else:
            links = Link.get_by_tag(tag, int(page))
        page = Page(links.count(), int(page))
        self.render('list.html', links=links, page=page)


class LinkGetInfoHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self, *args):
        url = self.get_argument('url')
        info = Link.get_info(url)
        if info:
            self.write(json.dumps({
                'success': 'true',
                'favicon': info['favicon'],
                'title': info['title'],
                'description': info['description'],
                'tags': info['tags'],
                'note': info['note']
                # 'is_star': info['is_star'],
                # 'is_readed': info['is_readed']
            }))
        else:
            self.write(json.dumps({'success': 'false'}))


class LinkGetDetailHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self, *args):
        url = self.get_argument('url')
        link = Link.get_by_url(url)
        if link:
            self.write(json.dumps({
                'success': 'true',
                'title': link['title'],
                'favicon': link['favicon'],
                'description': link['description'],
                'tags': ','.join(link['tags']),
                'note': link['note'],
                'article': link['article']
            }))
        else:
            self.write(json.dumps({'success': 'false'}))


class LinkRefreshHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self, *args):
        url = self.get_argument('url')
        link = Link.get_by_url(url)
        if link:
            link = Link.refresh(link)
            link = Link.insert_or_update(link)
            link_module = tornado.escape.to_basestring(
                self.render_string('modules/link.html', link=link))
            self.write(
                json.dumps({'success': 'true', 'link_module': link_module, 'title': link['title'], 'article': tornado.escape.to_basestring(link['article'])}))
        else:
            self.write(json.dumps({'success': 'false'}))


class LinkGetArticleHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self, *args):
        url = self.get_argument('url')
        link = Link.get_by_url(url)
        if link:
            if link['article'] == '':
                link = Link.refresh(link)
            self.write(json.dumps({
                'success': 'true',
                'title': link['title'],
                'article': link['article']
            }))
        else:
            self.write(json.dumps({'success': 'false'}))


class LinkAddHandler(BaseHandler):

    @tornado.web.authenticated
    def post(self, *args):
        note = self.get_argument('note')
        post_time = int(time.time())
        link = dict(
            url=self.get_argument('url'),
            title=self.get_argument('title'),
            favicon=self.get_argument('favicon'),
            tags=format_tags(self.get_argument('tags')),
            note=note,
            post_time=post_time,
            random=random.random(),
            html=self.get_argument('html')
        )
        link = Link.insert_or_update(link)
        link_module = tornado.escape.to_basestring(
            self.render_string('modules/link.html', link=link))
        self.write(json.dumps({'success': 'true', 'link_module': link_module, 'article': tornado.escape.to_basestring(link['article'])}))


class LinkDelHandler(BaseHandler):

    @tornado.web.authenticated
    def post(self, *args):
        url = self.get_argument('url')
        Link.delete(url)
        self.write(json.dumps({'success': 'true'}))


class TagLinksHandler(BaseHandler):

    def get(self, page, tag):
        tags = Link.get_tags()
        tags_cloud = get_tags_cloud(tags)
        links = Link.get_by_tag(tag, int(page))
        page = Page(links.count(), int(page))
        self.render('tags_links.html', tags_cloud=tags_cloud, links=links, count=Link.get_count(), page=page, cur_tag=tag, tag_count=links.count())


class TagsCloudHandler(BaseHandler):

    def get(self):
        tags = Link.get_tags()
        tags_cloud = get_tags_cloud(tags)
        self.render('tags_cloud.html', tags_cloud=tags_cloud)


class RandomLinksHandler(BaseHandler):

    def get(self):
        tags = Link.get_tags()
        tags_cloud = get_tags_cloud(tags)
        links = Link.get_random_links()
        self.render('random_links.html', tags_cloud=tags_cloud,
                    links=links, count=Link.get_count())


class RandomLinkHandler(BaseHandler):

    def get(self):
        link = Link.get_random_one()
        link_module = tornado.escape.to_basestring(
            self.render_string('modules/link.html', link=link))
        self.write(json.dumps({
            'success': 'true',
            'url': link['url'],
            'title': link['title'],
            'article': link['article'],
            'link_module': link_module
        }))


class SearchHandler(BaseHandler):
    """搜索书签
    """
    def get(self):
        tags = Link.get_tags()
        tags_cloud = get_tags_cloud(tags)
        keywords = self.get_argument('keywords')
        result = Link.get_by_keywords(keywords)
        count = result.count()
        self.render('search_result.html', keywords=keywords, tags_cloud=tags_cloud, links=result, count=count)
