#!/usr/bin/python
# -*- coding: utf-8 -*-

# Chrome Bookmark Exporter, tested with OS X Chrome 7.0.517.41
# Jan Eden <software (a) janeden net>
# based on a Groovy script by Dan Fraser [http://www.capybara.org/~dfraser/archives/355]
# This file is public domain. Python 2.6 or newer required

import json
import cgi
import codecs
import copy
from configs.config import config
from handlers.link import Link
import time
import os.path
# 数据库名
links_db = config['db'].links
# 书签路径
input_filename = os.path.abspath('.') + "/Bookmarks"
print(input_filename)


def loop_entrys(bookmarks, tags):
    """遍历所有书签
    """
    link_tags = ','.join(copy.deepcopy(tags))
    for entry in bookmarks:
        if entry['type'] == 'folder':
            if not len(entry['children']) == 0:
                tags.append(entry['name'])
                next_folder = entry['children']
                loop_entrys(next_folder, tags)
        else:
            link = Link.get_by_url(cgi.escape(entry['url']))
            if not link:
                link = dict(
                    url=cgi.escape(entry['url']),
                    title=entry['name'],
                    favicon='',
                    description=entry['name'],
                    tags=link_tags.split(','),
                    note='',
                    note_html='',
                    is_star=0,
                    is_readed=0,
                    post_time=int(time.time())
                )
                links_db.insert(link)
            else:
                link['tags'] = link_tags.split(',')
                links_db.save(link)
    tags.pop()


def add_links():
    """从Chrome书签导入"""
    try:
        input_file = codecs.open(input_filename, encoding='utf-8')
        bookmark_data = json.load(input_file)
        roots = bookmark_data['roots']
        for entry in roots:
            try:
                loop_entrys(roots[entry]['children'], [entry])
            except TypeError:
                print("not has children")
    except IOError:
        print('file not exist')


add_links()
